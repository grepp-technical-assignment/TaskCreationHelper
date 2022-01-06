#ifndef __RNUTIL_H__
#define __RNUTIL_H__

#include <sys/stat.h>
#include <string.h>
#include <stdio.h>

#include "rntype.h"
#include "rnsys.h"

VOID STDCALL check_system_function();
VOID STDCALL check_docker();
VOID STDCALL check_docker_daemon();
BOOL STDCALL is_exist(LPCSTR);
BOOL STDCALL is_dir(LPCSTR);
BOOL STDCALL is_absolute_path(LPCSTR);
BOOL STDCALL end_with(LPSTR, LPCSTR);

#endif // __RNUTIL_H__ //
