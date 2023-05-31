#CUDA_SDK_PATH = /af10/sc5nf/NVIDIA_CUDA_SDK

CXXFLAGS=-fsave-optimization-record -O3 -fopenmp -march=native
LDFLAGS=-L ${LLVM_INSTALL}/lib -Wl,--rpath,${LLVM_INSTALL}/lib

BUILD_WITH_APOLLO_CXXFLAGS=${CXXFLAGS} -Xclang -load -Xclang ${LLVM_INSTALL}/../lib/LLVMApollo.so -mllvm --apollo-omp-procbinds=close,spread -mllvm --apollo-omp-numthreads=${APOLLO_CPU_POLICIES}
BUILD_WITH_APOLLO_LDFLAGS=${LDFLAGS} -L ${APOLLO_INSTALL}/lib -Wl,--rpath,${APOLLO_INSTALL}/lib -lapollo 

CFLAGS=${CXXFLAGS} ${LDFLAGS}

CC=${LLVM_INSTALL}/bin/clang++
#CC=g++

#OMP_NUM_THREADS = 16
MIC_OMP_NUM_THREADS = 216

#all: euler3d_cpu euler3d_cpu_double pre_euler3d_cpu pre_euler3d_cpu_double euler3d_cpu_offload
all: euler3d_cpu euler3d_cpu_apollo euler3d_cpu_double euler3d_cpu_double_apollo

#euler3d: euler3d.cu
#	nvcc -Xptxas -v -O3 --gpu-architecture=compute_13 --gpu-code=compute_13 euler3d.cu -o euler3d -I$(CUDA_SDK_PATH)/common/inc  -L$(CUDA_SDK_PATH)/lib  -lcutil

#euler3d_double: euler3d_double.cu
#	nvcc -Xptxas -v -O3 --gpu-architecture=compute_13 --gpu-code=compute_13 euler3d_double.cu -o euler3d_double -I$(CUDA_SDK_PATH)/common/inc  -L$(CUDA_SDK_PATH)/lib  -lcutil

euler3d_cpu: euler3d_cpu.cpp
	mkdir -p buildNoApollo
	${CC} -O3 -Dblock_length=$(OMP_NUM_THREADS) ${CFLAGS} euler3d_cpu.cpp -o buildNoApollo/euler3d_cpu

euler3d_cpu_apollo: euler3d_cpu.cpp
	mkdir -p buildWithApollo
	${CC} -O3 -Dblock_length=$(OMP_NUM_THREADS) ${BUILD_WITH_APOLLO_CXXFLAGS} ${BUILD_WITH_APOLLO_LDFLAGS} euler3d_cpu.cpp -o buildWithApollo/euler3d_cpu

euler3d_cpu_double: euler3d_cpu_double.cpp
	mkdir -p buildNoApollo
	${CC} -O3 -Dblock_length=$(OMP_NUM_THREADS) ${CFLAGS} euler3d_cpu_double.cpp -o buildNoApollo/euler3d_cpu_double

euler3d_cpu_double_apollo: euler3d_cpu_double.cpp
	mkdir -p buildWithApollo
	${CC} -O3 -Dblock_length=$(OMP_NUM_THREADS) ${BUILD_WITH_APOLLO_CXXFLAGS} ${BUILD_WITH_APOLLO_LDFLAGS} euler3d_cpu_double.cpp -o buildWithApollo/euler3d_cpu_double

#pre_euler3d: pre_euler3d.cu
#	nvcc -Xptxas -v -O3 --gpu-architecture=compute_13 --gpu-code=compute_13 pre_euler3d.cu -o pre_euler3d -I$(CUDA_SDK_PATH)/common/inc  -L$(CUDA_SDK_PATH)/lib  -lcutil

#pre_euler3d_double: pre_euler3d_double.cu
#	nvcc -Xptxas -v -O3 --gpu-architecture=compute_13 --gpu-code=compute_13 pre_euler3d_double.cu -o pre_euler3d_double -I$(CUDA_SDK_PATH)/common/inc  -L$(CUDA_SDK_PATH)/lib  -lcutil

#pre_euler3d_cpu: pre_euler3d_cpu.cpp
## ${CC} -O3 -Dblock_length=$(OMP_NUM_THREADS) -fopenmp pre_euler3d_cpu.cpp -o pre_euler3d_cpu
#	${CC} -O3 -Dblock_length=$(OMP_NUM_THREADS) ${CFLAGS} pre_euler3d_cpu.cpp -o pre_euler3d_cpu
#
#pre_euler3d_cpu_double: pre_euler3d_cpu_double.cpp
## ${CC} -O3 -Dblock_length=$(OMP_NUM_THREADS) -fopenmp pre_euler3d_cpu_double.cpp -o pre_euler3d_cpu_double
#	${CC} -O3 -Dblock_length=$(OMP_NUM_THREADS) ${CFLAGS} pre_euler3d_cpu_double.cpp -o pre_euler3d_cpu_double


clean:
	rm -f buildWithApollo/euler3d_cpu
	rm -f buildWithApollo/euler3d_cpu_double
	rm -f buildNoApollo/euler3d_cpu
	rm -f buildNoApollo/euler3d_cpu_double

