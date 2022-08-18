#ifndef __RUNNER_H__
#define __RUNNER_H__

#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>

#include "rnutil.h"
#include "rntype.h"
#include "rnsys.h"

#define RUNNER_VERSION "v0.3.0"

#define CONFIG_FILE "config.json"

#define MAX_CL_LEN 1024

#define STATEMENT_BUF_SIZE (1 << 14)

static LPCSTR statement_filter_str[] = {
    "", "",
};

enum level_t {
    GENERATE,
    PRODUCE,
    STRESS,
    FULL,
    INVOCATE,
};

struct config_t {
    CHAR cmd[MAX_CL_LEN];
    CHAR path[MAX_CL_LEN];
    enum level_t level;
    BOOL initialize;
    BOOL text_filter;
    BOOL pause_on_err;
    BOOL reduced_debug;
    LPCSTR stress_index;
};

VOID STDCALL print_usage();
VOID STDCALL print_version();

VOID STDCALL parse_args(struct config_t*, int, char**);
VOID STDCALL make_path(struct config_t*);
VOID STDCALL make_run_command(struct config_t*);
VOID STDCALL run_command(struct config_t*);
VOID STDCALL generate_config(struct config_t*);
VOID STDCALL generate_statement(struct config_t*);
VOID STDCALL filtering_text(struct config_t*);

#endif // __RUNNER_H__ //
