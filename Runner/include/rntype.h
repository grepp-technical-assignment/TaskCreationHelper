#ifndef __RNLIB_H__
#define __RNLIB_H__

#if defined(__i386__) && (defined(__clang__) || defined(__GNUC__))
#define STDCALL __attribute__((stdcall))
#else
#define STDCALL
#endif

#define TRUE            1
#define FALSE           0

typedef int             INT;
typedef char            CHAR;
typedef void            VOID;
typedef INT             BOOL;

typedef CHAR*           LPSTR;
typedef const CHAR*     LPCSTR;

typedef unsigned int    SIZE_T;

#endif // __RNLIB_H__
