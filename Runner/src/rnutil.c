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
    if (SYSTEM("docker --version > " DEVNULL " 2>&1")) {
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
    if (SYSTEM("docker images > " DEVNULL " 2>&1")) {
        printf("tch: docker daemon is not running\n");
        exit(EXIT_FAILURE);
    }
}

/**
 * @brief Make directory recursively
 * 
 * @param path - directory path to make (path must be absolute path)
 * @param mode - directory mode
 * @return BOOL - TRUE if make directory successfully, FALSE if not
 */
BOOL STDCALL make_dir(LPCSTR path, mode_t mode) {
    CHAR tmp_path[MAX_CL_LEN]; tmp_path[0] = 0;
    INT index_stack[MAX_CL_LEN]; index_stack[0] = 0;

    if (path == NULL) return TRUE;
    if (!is_absolute_path(path)) return FALSE;

    memcpy(tmp_path, path, sizeof tmp_path);
    INT n = strlen(path), index_len = 0;
    BOOL recovery = FALSE;
    
    // make path recursively
    if (tmp_path[n - 1] == FILE_SLASH_C) tmp_path[--n] = 0;
    for (INT i = 0; i <= n; ++i) {
        if (i > 0 && (tmp_path[i] == FILE_SLASH_C || i == n)) {
            tmp_path[i] = 0;
            if (!is_dir(tmp_path)) {
                if (mkdir(tmp_path, mode) == -1) {
                    recovery = TRUE;
                    break;
                }
                index_stack[index_len++] = i;
            }
            if (i != n) tmp_path[i] = FILE_SLASH_C;
        }
    }

    // remove created directory recursively
    if (recovery) {
        for (INT i = index_len; i--; ) {
            tmp_path[index_stack[i]] = 0;
            remove(tmp_path);
        }
        return FALSE;
    }
    return TRUE;
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
 * @brief Check path is absolute or relative
 * 
 * @param path - path to check
 * @return BOOL - TRUE if path is absolute, FALSE if not
 */
BOOL STDCALL is_absolute_path(LPCSTR path) {
#if defined(__linux__) || defined(__APPLE__)
    return path[0] == FILE_SLASH_C;
#elif defined(_WIN32) || defined(_WIN64)
    INT sz = strlen(path);
    return (path[0] == FILE_SLASH_C) || (sz > 2 && path[1] == ':' && path[2] == FILE_SLASH_C);
#else
    puts("tch: unknown system");
    exit(EXIT_FAILURE);
#endif
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
