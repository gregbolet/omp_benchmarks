CC=clang++

CXXFLAGS=-g -O3 -fopenmp -march=native -I /p/vast1/ggeorgak/projects/apollo/omp_benchmarks 
LDFLAGS=-L /p/vast1/ggeorgak/projects/apollo/apollo/build-quartz/install/lib -Wl,--rpath,/p/vast1/ggeorgak/projects/apollo/apollo/build-quartz/install/lib -lapollo

all: bfs

bfs: bfs.cpp
	$(CC) ${CXXFLAGS} bfs.cpp -o bfs.x ${LDFLAGS}
	#$(CC) ${CXXFLAGS} ${LDFLAGS} bfs.cpp -o bfs.x

clean:
	rm -f build*/bfs *.yaml *.o build*/result.txt
