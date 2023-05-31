#!/bin/bash

CXXFLAGS=-fsave-optimization-record -O3 -fopenmp -march=native
LDFLAGS=-L ${LLVM_INSTALL}/lib -Wl,--rpath,${LLVM_INSTALL}/lib

BUILD_WITH_APOLLO_CXXFLAGS=${CXXFLAGS} -Xclang -load -Xclang ${LLVM_INSTALL}/../lib/LLVMApollo.so -mllvm --apollo-omp-procbinds=close,spread -mllvm --apollo-omp-numthreads=${APOLLO_CPU_POLICIES}
BUILD_WITH_APOLLO_LDFLAGS=${LDFLAGS} -L ${APOLLO_INSTALL}/lib -Wl,--rpath,${APOLLO_INSTALL}/lib -lapollo 

cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_COMPILER=${LLVM_INSTALL}/bin/clang++ \
    -DCMAKE_C_COMPILER=${LLVM_INSTALL}/bin/clang \
    -DWITH_MPI=off \
    -DWITH_OPENMP=on \
    -DCMAKE_EXE_LINKER_FLAGS="-L ${LLVM_INSTALL}/lib -Wl,--rpath,${LLVM_INSTALL}/lib ${BUILD_WITH_APOLLO_LDFLAGS}" \
    -DCMAKE_CXX_FLAGS="${BUILD_WITH_APOLLO_CXXFLAGS}" \
    ..
