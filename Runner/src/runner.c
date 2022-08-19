#include "runner.h"

/**
 * @brief print usage
 * 
 * @return VOID 
 */
VOID STDCALL print_usage() {
    printf("usage: tch [-h] [-v] [-l LEVEL] [-s STRESS_INDEX] [-p] [-r] [-i] PATH\n");
    printf("\n");
    printf("optional arguments:\n");
    printf("%-24s%s", "  -h, --help", "Show this help message\n");
    printf("%-24s%s", "  -v, --version", "Show the version of tch runner & TCH\n");
    printf("%s\n%-24s%s", "  -l LEVEL, --level LEVEL", "", "Specify the level of TCH execution (generate - produce - stress - full - invocate) [default LEVEL = full]\n");
    printf("%s\n%-24s%s", "  -s STRESS_INDEX, --stress_index STRESS_INDEX", "", "Specify the index of stress\n");
    printf("%-24s%s", "  -p, --pause_on_err", "Pause on error\n");
    printf("%-24s%s", "  -r, --reduced_debug", "Reduce amount of debugging\n");
    printf("%-24s%s", "  -i, --init", "Initialize Problem Repository in PATH\n");
    printf("%-24s%s", "  -t, --text_filter", "Filtering Problem Statement in PATH\n");
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
    config->initialize = FALSE;
    config->text_filter = FALSE;

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
            } else if (strcmp(argv[i], "-i") == 0 || strcmp(argv[i], "--init") == 0) {
                config->initialize = TRUE;
            } else if (strcmp(argv[i], "-t") == 0 || strcmp(argv[i], "--text_filter") == 0) {
                config->text_filter = TRUE;
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

    if (config->initialize) {
        // check path is not exist or not
        if (is_exist(config->path) && is_dir(config->path)) {
            printf("tch: can't initialize problem repository in '%s'. path is already exist\n", config->path);
            exit(EXIT_FAILURE);
        }
    } else {
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
    if (config->initialize) { // initialize problem repository
        config->cmd[0] = 0;
    } else { // run tch
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
}

/**
 * @brief run command
 * 
 * @param config - config
 * @return VOID 
 */
VOID STDCALL run_command(struct config_t* config) {
    if (config->text_filter) { // filtering text to plain text
        filtering_text(config);
    } else if (config->initialize) { // initialize problem repository
        generate_config(config);
        generate_statement(config);
    } else if (SYSTEM(config->cmd)) { // run tch
        printf("tch: tch run error\n");
        exit(EXIT_FAILURE);
    }
}


/**
 * @brief generate config file in path/config.json
 * 
 * @param config - config
 * @return VOID 
 */
VOID STDCALL generate_config(struct config_t* config) {
    CHAR config_path[MAX_CL_LEN]; config_path[0] = 0;

    // initialize file path
    sprintf(config_path,
        "%s%sconfig.json",
        config->path,
        (config->path[strlen(config->path) - 1] == FILE_SLASH_C ? "" : FILE_SLASH_S)
    );

    // build directory
    if (!make_dir(config->path, 0755)) {
        printf("tch: can't create directory '%s'\n", config->path);
        exit(EXIT_FAILURE);
    }

    // write config file
    FILE* fp = fopen(config_path, "w");
    if (fp == NULL) {
        printf("tch: can't write file in '%s'\n", config_path);
        exit(EXIT_FAILURE);
    }

    fprintf(fp,
#include "default_config"
    );

    printf("tch: config file is generated\n");

    fclose(fp);
}

/**
 * @brief generate statement file in path/statement.md
 * 
 * @param config 
 * @return VOID 
 */
VOID STDCALL generate_statement(struct config_t* config) {
    CHAR statement_path[MAX_CL_LEN]; statement_path[0] = 0;

    // initialize file path
    sprintf(statement_path,
        "%s%sstatement.md",
        config->path,
        (config->path[strlen(config->path) - 1] == FILE_SLASH_C ? "" : FILE_SLASH_S)
    );

    // write statement file
    FILE* fp = fopen(statement_path, "w");
    if (fp == NULL) {
        printf("tch: can't write file in '%s'\n", statement_path);
        exit(EXIT_FAILURE);
    }

    fprintf(fp,
#include "default_statement"
    );

    printf("tch: statement file is generated\n");

    fclose(fp);
}

/**
 * @brief filtering text file in path/statement.md
 *  remove invisible special characters from macOS
 * TODO: Need to handling unicode characters
 *  if i write statement.md file length upper than STATEMENT_BUF_SIZE
 *  then error occurred
 * 
 * @param config 
 * @return VOID 
 */
VOID STDCALL filtering_text(struct config_t* config) {
    CHAR statement_path[MAX_CL_LEN];
    CHAR filtered_statement_path[MAX_CL_LEN];
    statement_path[0] = 0;
    filtered_statement_path[0] = 0;

    // initialize file path
    sprintf(statement_path,
        "%s%sstatement.md",
        config->path,
        (config->path[strlen(config->path) - 1] == FILE_SLASH_C ? "" : FILE_SLASH_S)
    );
    sprintf(filtered_statement_path,
        "%s%sTCH_filtered_statement.md",
        config->path,
        (config->path[strlen(config->path) - 1] == FILE_SLASH_C ? "" : FILE_SLASH_S)
    );

    INT deleted_count = 0;

    FILE* fp = fopen(statement_path, "r");
    if (fp == NULL) {
        printf("tch: can't read statement file in '%s'\n", statement_path);
        exit(EXIT_FAILURE);
    }
    FILE* outp = fopen(filtered_statement_path, "w");
    if (outp == NULL) {
        printf("tch: can't write filtered statement file in '%s'\n", filtered_statement_path);
        exit(EXIT_FAILURE);
    }
    for (; !feof(fp); ) {
        CHAR buf[STATEMENT_BUF_SIZE + 4]; buf[0] = 0;
        SIZE_T read_size;
        read_size = fread(buf, sizeof(CHAR), STATEMENT_BUF_SIZE, fp);
        if (read_size == 0) {
            printf("tch: statement file read error\n");
            exit(EXIT_FAILURE);
        }
        buf[read_size] = 0;
        for (INT i = sizeof statement_filter_str / sizeof(LPCSTR); i--; ) {
            for (; ;) {
                LPSTR pivot = strstr(buf, statement_filter_str[i]);
                if (pivot == NULL) break;
                ++deleted_count;
                SIZE_T filter_size = strlen(statement_filter_str[i]);
                SIZE_T pindex = pivot - buf;
                memmove(pivot, pivot + filter_size, sizeof(CHAR) * (read_size + 1 - pindex - filter_size));
                read_size -= filter_size;
            }
        }
        fwrite(buf, sizeof(CHAR), read_size, outp);
    }
    fclose(fp);
    fclose(outp);

    printf("tch: special characters deleted count = %d\n", deleted_count);
    printf("tch: TCH_filtered_statement file is generated\n");
}
