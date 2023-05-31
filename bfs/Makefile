CC=${LLVM_INSTALL}/bin/clang++

CXXFLAGS=-fsave-optimization-record -O3 -fopenmp -march=native
LDFLAGS=-L ${LLVM_INSTALL}/lib -Wl,--rpath,${LLVM_INSTALL}/lib

BUILD_WITH_APOLLO_CXXFLAGS=${CXXFLAGS} -Xclang -load -Xclang ${LLVM_INSTALL}/../lib/LLVMApollo.so -mllvm --apollo-omp-procbinds=close,spread -mllvm --apollo-omp-numthreads=${APOLLO_CPU_POLICIES}
BUILD_WITH_APOLLO_LDFLAGS=${LDFLAGS} -L ${APOLLO_INSTALL}/lib -Wl,--rpath,${APOLLO_INSTALL}/lib -lapollo 

all: bfs bfs_apollo

bfs: bfs.cpp
	mkdir -p buildNoApollo
	$(CC) ${CXXFLAGS} ${LDFLAGS} bfs.cpp -o buildNoApollo/bfs 

bfs_apollo: bfs.cpp 
	mkdir -p buildWithApollo
	$(CC) ${BUILD_WITH_APOLLO_CXXFLAGS} ${BUILD_WITH_APOLLO_LDFLAGS} bfs.cpp -o buildWithApollo/bfs 

clean:
	rm -f build*/bfs *.yaml *.o build*/result.txt
