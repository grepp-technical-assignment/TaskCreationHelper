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

enum level_t {
    GENERATE,
    PRODUCE,
    STRESS,
    FULL,
    INVOCATE,
};

static LPCSTR level_t_name[] = {
    "generate",
    "produce",
    "stress",
    "full",
    "invocate",
};

#endif // __RNLIB_H__
