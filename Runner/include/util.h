#ifndef __UTIL_H__
#define __UTIL_H__

#include <sys/stat.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include "rntype.h"
#include "rnsys.h"

VOID STDCALL check_system_function();
VOID STDCALL check_docker();
BOOL STDCALL is_exist(LPCSTR);
BOOL STDCALL is_dir(LPCSTR);
BOOL STDCALL end_with(LPSTR, LPCSTR);

#endif // __UTIL_H__ //
