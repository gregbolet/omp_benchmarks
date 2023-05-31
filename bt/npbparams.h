/* CLASS = D */
/*
   This file is generated automatically by the setparams utility.
   It sets the number of processors and the class of the NPB
   in this directory. Do not modify it by hand.   
*/
#define PROBLEM_SIZE   408
#define NITER_DEFAULT  250
#define DT_DEFAULT     0.00002

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
