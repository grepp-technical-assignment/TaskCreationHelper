#include "runner.h"

/**
 * @brief console main application
 * 
 * @param argc - number of arguments
 * @param argv - arguments
 * @return int - exit code
 */
int main(int argc, char** argv) {
#ifndef __TCH_SUPPORTED_OS__
    puts("tch: unknown system");
    exit(EXIT_FAILURE);
#endif
    struct config_t config;

    // check system & docker //
    check_system_function();
    check_docker();
    check_docker_daemon();
    // TODO: check docker images is installed

    // parse arguments //
    parse_args(&config, argc, argv);
    make_path(&config);

    // run tch //
    make_run_command(&config);
    run_command(&config);
    return 0;
}
