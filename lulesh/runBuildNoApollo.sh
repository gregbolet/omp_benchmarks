#!/bin/bash

CXXFLAGS="-fsave-optimization-record -O3 -fopenmp -march=native"
LDFLAGS="-L ${LLVM_INSTALL}/lib -Wl,--rpath,${LLVM_INSTALL}/lib"

BUILD_NO_APOLLO_CXXFLAGS=${CXXFLAGS}
BUILD_NO_APOLLO_LDFLAGS=${LDFLAGS}

cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_COMPILER=${LLVM_INSTALL}/bin/clang++ \
    -DCMAKE_C_COMPILER=${LLVM_INSTALL}/bin/clang \
    -DWITH_MPI=off \
    -DWITH_OPENMP=on \
    -DCMAKE_EXE_LINKER_FLAGS="${BUILD_NO_APOLLO_LDFLAGS}" \
    -DCMAKE_CXX_FLAGS="${BUILD_NO_APOLLO_CXXFLAGS}" \
    ..