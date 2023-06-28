#!/bin/bash

CXXFLAGS="-fopenmp -march=native -I ${ROOT_DIR} -DENABLE_APOLLO -gdwarf-4"
LDFLAGS="-L ${APOLLO_INSTALL}/lib -Wl,--rpath,${APOLLO_INSTALL}/lib -lapollo"

UNAME=$(uname -n)

if [[ $name == *"ruby"* ]]; then 
	echo "RUBY Machine Detected";
	CXXFLAGS = "${CXXFLAGS} -DRUBY_MACHINE"
elif [[ $name == *"lassen"* ]]; then
	echo "LASSEN Machine Detected";
	CXXFLAGS = "${CXXFLAGS} -DLASSEN_MACHINE"
fi

cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_COMPILER=clang++ \
    -DWITH_MPI=off \
    -DWITH_OPENMP=on \
    -DCMAKE_EXE_LINKER_FLAGS="${LDFLAGS}" \
    -DCMAKE_CXX_FLAGS="${CXXFLAGS}" \
    ..
