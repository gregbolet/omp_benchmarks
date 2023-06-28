#CUDA_SDK_PATH = /af10/sc5nf/NVIDIA_CUDA_SDK

CXXFLAGS=-O3 -fopenmp -march=native -I ${ROOT_DIR}

APOLLO_CXXFLAGS=$(CXXFLAGS) -DENABLE_APOLLO
APOLLO_LDFLAGS=-L ${APOLLO_INSTALL}/lib -Wl,--rpath,${APOLLO_INSTALL}/lib -lapollo 

UNAME=$(shell uname -n)
ifneq (,$(findstring ruby,$(UNAME)))
 	$(info building RUBY)
	APOLLO_CXXFLAGS += -DRUBY_MACHINE
else ifneq (,$(findstring lassen,$(UNAME)))
 	$(info building LASSEN)
	APOLLO_CXXFLAGS += -DLASSEN_MACHINE
endif

CXX=clang++

# TODO: BLOCK_LENGTH seems to be originally the same as number of threads
# OMP_NUM_THREADS, how would this work with dynamic thread setting?
BLOCK_LENGTH=72

#all: euler3d_cpu euler3d_cpu_double pre_euler3d_cpu pre_euler3d_cpu_double euler3d_cpu_offload
all: euler3d_cpu euler3d_cpu_apollo euler3d_cpu_double euler3d_cpu_double_apollo

#euler3d: euler3d.cu
#	nvcc -Xptxas -v -O3 --gpu-architecture=compute_13 --gpu-code=compute_13 euler3d.cu -o euler3d -I$(CUDA_SDK_PATH)/common/inc  -L$(CUDA_SDK_PATH)/lib  -lcutil

#euler3d_double: euler3d_double.cu
#	nvcc -Xptxas -v -O3 --gpu-architecture=compute_13 --gpu-code=compute_13 euler3d_double.cu -o euler3d_double -I$(CUDA_SDK_PATH)/common/inc  -L$(CUDA_SDK_PATH)/lib  -lcutil

euler3d_cpu: euler3d_cpu.cpp
	mkdir -p buildNoApollo
	${CXX} -Dblock_length=$(BLOCK_LENGTH) ${CXXFLAGS} euler3d_cpu.cpp -o buildNoApollo/euler3d_cpu

euler3d_cpu_apollo: euler3d_cpu.cpp
	mkdir -p buildWithApollo
	${CXX} -Dblock_length=$(BLOCK_LENGTH) $(APOLLO_CXXFLAGS) euler3d_cpu.cpp -o buildWithApollo/euler3d_cpu $(APOLLO_LDFLAGS)

euler3d_cpu_double: euler3d_cpu_double.cpp
	mkdir -p buildNoApollo
	${CXX} -Dblock_length=$(BLOCK_LENGTH) $(CXXFLAGS) euler3d_cpu_double.cpp -o buildNoApollo/euler3d_cpu_double

euler3d_cpu_double_apollo: euler3d_cpu_double.cpp
	mkdir -p buildWithApollo
	${CXX} -Dblock_length=$(BLOCK_LENGTH) $(APOLLO_CXXFLAGS) euler3d_cpu_double.cpp -o buildWithApollo/euler3d_cpu_double $(APOLLO_LDFLAGS)

#pre_euler3d: pre_euler3d.cu
#	nvcc -Xptxas -v -O3 --gpu-architecture=compute_13 --gpu-code=compute_13 pre_euler3d.cu -o pre_euler3d -I$(CUDA_SDK_PATH)/common/inc  -L$(CUDA_SDK_PATH)/lib  -lcutil

#pre_euler3d_double: pre_euler3d_double.cu
#	nvcc -Xptxas -v -O3 --gpu-architecture=compute_13 --gpu-code=compute_13 pre_euler3d_double.cu -o pre_euler3d_double -I$(CUDA_SDK_PATH)/common/inc  -L$(CUDA_SDK_PATH)/lib  -lcutil

#pre_euler3d_cpu: pre_euler3d_cpu.cpp
## ${CXX} -O3 -Dblock_length=$(BLOCK_LENGTH) -fopenmp pre_euler3d_cpu.cpp -o pre_euler3d_cpu
#	${CXX} -O3 -Dblock_length=$(BLOCK_LENGTH) ${CXXFLAGS} pre_euler3d_cpu.cpp -o pre_euler3d_cpu
#
#pre_euler3d_cpu_double: pre_euler3d_cpu_double.cpp
## ${CXX} -O3 -Dblock_length=$(BLOCK_LENGTH) -fopenmp pre_euler3d_cpu_double.cpp -o pre_euler3d_cpu_double
#	${CXX} -O3 -Dblock_length=$(BLOCK_LENGTH) ${CXXFLAGS} pre_euler3d_cpu_double.cpp -o pre_euler3d_cpu_double


clean:
	rm -f buildWithApollo/euler3d_cpu
	rm -f buildWithApollo/euler3d_cpu_double
	rm -f buildNoApollo/euler3d_cpu
	rm -f buildNoApollo/euler3d_cpu_double

