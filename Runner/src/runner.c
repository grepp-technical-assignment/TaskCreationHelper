#include "runner.h"

/**
 * @brief print usage
 * 
 * @return VOID 
 */
VOID STDCALL print_usage() {
    printf("usage: tch [-h] [-v] [-l LEVEL] [-s STRESS_INDEX] [-p] [-r] PATH\n");
    printf("\n");
    printf("optional arguments:\n");
    printf("%-24s%s", "  -h, --help", "Show this help message\n");
    printf("%-24s%s", "  -v, --version", "Show the version of tch runner & TCH\n");
    printf("%s\n%-24s%s", "  -l LEVEL, --level LEVEL", "", "Specify the level of TCH execution (generate - produce - stress - full - invocate) [default LEVEL = full]\n");
    printf("%s\n%-24s%s", "  -s STRESS_INDEX, --stress_index STRESS_INDEX", "", "Specify the index of stress\n");
    printf("%-24s%s", "  -p, --pause_on_err", "Pause on error\n");
    printf("%-24s%s", "  -r, --reduced_debug", "Reduce amount of debugging\n");
    printf("%-24s%s", "  PATH", "Relative path to the TCH project\n");
}

/**
 * @brief print runner version & tch version
 * 
 * @return VOID 
 */
VOID STDCALL print_version() {
#ifndef TCH_VERSION // This macro will be define in compiler option
#define TCH_VERSION "Unknown"
#endif
    printf("TaskCreationHelper v%s\n", TCH_VERSION);
    printf("tch-runner %s\n", RUNNER_VERSION);
}

/**
 * @brief parse command line arguments & setup config or print helper message
 * 
 * @param config - config
 * @param argc - number of arguments
 * @param argv - arguments
 * @return VOID 
 */
VOID STDCALL parse_args(struct config_t* config, int argc, char** argv) {
    config->cmd[0] = 0;
    config->path[0] = 0;
    config->level = FULL;
    config->pause_on_err = FALSE;
    config->reduced_debug = FALSE;
    config->stress_index = NULL;

    for (int i = 1; i < argc; ++i) {
        if (argv[i][0] == '-') {
            if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
                print_usage();
                exit(EXIT_SUCCESS);
            } else if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--version") == 0) {
                print_version();
                exit(EXIT_SUCCESS);
            } else if (strcmp(argv[i], "-l") == 0 || strcmp(argv[i], "--level") == 0) {
                if (i + 1 < argc) {
                    if (strcmp(argv[i + 1], "generate") == 0) {
                        config->level = GENERATE;
                    } else if (strcmp(argv[i + 1], "produce") == 0) {
                        config->level = PRODUCE;
                    } else if (strcmp(argv[i + 1], "stress") == 0) {
                        config->level = STRESS;
                    } else if (strcmp(argv[i + 1], "full") == 0) {
                        config->level = FULL;
                    } else if (strcmp(argv[i + 1], "invocate") == 0) {
                        config->level = INVOCATE;
                    } else {
                        printf("tch: unknown level\n");
                        exit(EXIT_FAILURE);
                    }
                    ++i;
                } else {
                    printf("tch: missing level\n");
                    exit(EXIT_FAILURE);
                }
            } else if (strcmp(argv[i], "-s") == 0 || strcmp(argv[i], "--stress_index") == 0) {
                if (i + 1 < argc) {
                    config->stress_index = argv[i + 1];
                    ++i;
                } else {
                    printf("tch: missing stress index\n");
                    exit(EXIT_FAILURE);
                }
            } else if (strcmp(argv[i], "-p") == 0 || strcmp(argv[i], "--pause_on_err") == 0) {
                config->pause_on_err = TRUE;
            } else if (strcmp(argv[i], "-r") == 0 || strcmp(argv[i], "--reduced_debug") == 0) {
                config->reduced_debug = TRUE;
            } else {
                printf("tch: unknown argument '%s'\n", argv[i]);
                exit(EXIT_FAILURE);
            }
        } else {
            if (config->path[0] != 0) {
                printf("tch: two paths are given\n");
                exit(EXIT_FAILURE);
            }
            strcpy(config->path, argv[i]);
        }
    }
}

/**
 * @brief make path to absolute path
 * 
 * @param config - config
 * @return VOID 
 */
VOID STDCALL make_path(struct config_t* config) {
    CHAR cwd[MAX_CL_LEN]; cwd[0] = 0;

    if (config->path[0] == 0) {
        printf("tch: no input path\n");
        exit(EXIT_FAILURE);
    }
    // cut off the last slash
    for (INT ln = (INT)strlen(config->path) - 1; ln > 0 && config->path[ln] == FILE_SLASH_C; --ln) {
        config->path[ln] = 0;
    }

    // if not absolute path then get current working directory
    if (!is_absolute_path(config->path)) {
        if (getcwd(cwd, sizeof(cwd)) == NULL) {
            printf("tch: getcwd error\n");
            exit(EXIT_FAILURE);
        }
        strcat(cwd, FILE_SLASH_S);
        strcat(cwd, config->path);
        memcpy(config->path, cwd, sizeof config->path);
    }

    // check path is exist or not
    if (!is_exist(config->path)) {
        printf("tch: path '%s' is not exist\n", config->path);
        exit(EXIT_FAILURE);
    }

    // if path is not directory then check if target file is config file or not
    if (!is_dir(config->path)) {
        // if target file is config file then run tch
        if (end_with(config->path, CONFIG_FILE)) {
            // change to directory of config file
            config->path[strlen(config->path) - strlen(CONFIG_FILE)] = 0; // works fine without this line
        } else {
            printf("tch: path '%s' is not a directory & not a config file\n", config->path);
            exit(EXIT_FAILURE);
        }
    }
}

/**
 * @brief make docker run command
 * 
 * @param config - config
 * @return VOID 
 */
VOID STDCALL make_run_command(struct config_t* config) {
    LPCSTR level_t_name[] = {
        "generate",
        "produce",
        "stress",
        "full",
        "invocate",
    };
    sprintf(config->cmd,
        "docker run --name TCH_RUNNER --rm -it "
        "-v %s:/TCH/VOLUME "    // path
        "tch:latest -l %s"      // level
        "%s%s"                  // stress index
        "%s"                    // pause on err
        "%s "                   // reduced debug
        "-c VOLUME/config.json",
        
        config->path,
        level_t_name[config->level],
        (config->stress_index != NULL ? " -s" : ""),
            (config->stress_index != NULL ? config->stress_index : ""),
        (config->pause_on_err ? " -p" : ""),
        (config->reduced_debug ? " -r" : "")
    );
}

/**
 * @brief run command
 * 
 * @param config - config
 * @return VOID 
 */
VOID STDCALL run_command(struct config_t* config) {
    if (SYSTEM(config->cmd)) {
        printf("tch: tch run error\n");
        exit(EXIT_FAILURE);
    }
}
