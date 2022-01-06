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
 */
#if defined(__linux__)
    #define __TCH_SUPPORTED_OS__
    #define SYSTEM system
#elif defined(__APPLE__)
    #define __TCH_SUPPORTED_OS__
    #define SYSTEM system
#elif defined(_WIN32)
    #define __TCH_SUPPORTED_OS__
    #define SYSTEM system
#elif defined(_WIN64)
    #define __TCH_SUPPORTED_OS__
    #define SYSTEM system
#endif

#endif // __RNSYS_H__ //
