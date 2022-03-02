#ifndef __RNSYS_H__
#define __RNSYS_H__

#include <stdlib.h>

/**
 * [os list]
 *  __linux__       Defined on Linux
 *  __sun           Defined on Solaris
 *  __FreeBSD__     Defined on FreeBSD
 *  __NetBSD__      Defined on NetBSD
 *  __OpenBSD__     Defined on OpenBSD
 *  __APPLE__       Defined on Mac OS X
 *  __hpux          Defined on HP-UX
 *  __osf__         Defined on Tru64 UNIX (formerly DEC OSF1)
 *  __sgi           Defined on Irix
 *  _AIX            Defined on AIX
 *  _WIN32          Defined on Windows
 * 
 * checking os type
 * 
 * Warn: If you append new supported os, then you need to change "rnutil.c: is_absolute_path()"
 */
#if defined(__linux__) || defined(__APPLE__)
    #define __TCH_SUPPORTED_OS__
    #define SYSTEM system
    #define DEVNULL "/dev/null"
    #define FILE_SLASH_S "/"
    #define FILE_SLASH_C '/'
    #define MK_DIR(dir, mode) mkdir((dir), (mode))
#elif defined(_WIN32) || defined(_WIN64)
    #define __TCH_SUPPORTED_OS__
    #define SYSTEM system
    #define DEVNULL "nul"
    #define FILE_SLASH_S "\\"
    #define FILE_SLASH_C '\\'
    #define MK_DIR(dir, mode) mkdir(dir)
#endif

#endif // __RNSYS_H__ //
