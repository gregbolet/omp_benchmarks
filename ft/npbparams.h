/* CLASS = D */
/*
   This file is generated automatically by the setparams utility.
   It sets the number of processors and the class of the NPB
   in this directory. Do not modify it by hand.   
*/
#define NX             2048
#define NY             1024
#define NZ             1024
#define MAXDIM         2048
#define NITER_DEFAULT  25
#define NXP            2049
#define NYP            1024
#define NTOTAL         2147483648
#define NTOTALP        2148532224

#define CONVERTDOUBLE  false
#define COMPILETIME "01 Jun 2023"
#define NPBVERSION "3.3.1"
#define CS1 "${LLVM_INSTALL}/bin/clang"
#define CS2 "$(CC)"
#define CS3 "-lm"
#define CS4 "-I../npb_common "
#define CS5 "-Wall -O3 -fopenmp -mcmodel=medium ${CXXFLAGS}"
#define CS6 "-O3 -fopenmp -mcmodel=medium ${LDFLAGS}"
#define CS7 "randdp"
