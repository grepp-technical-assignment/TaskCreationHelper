#include "rnutil.h"

/**
 * @brief Check if system function is supported
 * 
 * Exit if not supported
 * 
 * @return VOID 
 */
VOID STDCALL check_system_function() {
    if (!SYSTEM(NULL)) {
        printf("tch: system function error\n");
        exit(EXIT_FAILURE);
    }
}

/**
 * @brief check if docker is installed
 * 
 * Exit if not installed
 * 
 * @return VOID 
 */
VOID STDCALL check_docker() {
    if (SYSTEM("docker --version > /dev/null 2>&1")) {
        printf("tch: docker is not installed\n");
        exit(EXIT_FAILURE);
    }
}

/**
 * @brief check if docker daemon is running
 * 
 * Exit if not running
 * 
 * @return VOID 
 */
VOID STDCALL check_docker_daemon() {
    if (SYSTEM("docker images > /dev/null 2>&1")) {
        printf("tch: docker daemon is not running\n");
        exit(EXIT_FAILURE);
    }
}


/**
 * @brief Check dir is exist or not
 * 
 * @param dir - dir or path to check
 * @return BOOL - TRUE if dir is exist, FALSE if not
 */
BOOL STDCALL is_exist(LPCSTR dir) {
    struct stat sb;

    if (stat(dir, &sb) == 0) return TRUE;
    return FALSE;
}

/**
 * @brief Check dir is directory or not
 * 
 * @param dir - dir or path to check
 * @return BOOL - TRUE if dir is directory, FALSE if not
 */
BOOL STDCALL is_dir(LPCSTR dir) {
    struct stat sb;

    if (stat(dir, &sb) == 0 && S_ISDIR(sb.st_mode)) return TRUE;
    return FALSE;
}

/**
 * @brief check if the str is end with
 * 
 * @param str - string to check
 * @param end - end string
 * @return BOOL 
 */
BOOL STDCALL end_with(LPSTR str, LPCSTR end) {
    INT slen = strlen(str), elen = strlen(end);
    if (slen < elen) return FALSE;
    return strcmp(str + slen - elen, end) == 0;
}
