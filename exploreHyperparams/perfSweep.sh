#!/bin/bash

PROG_TO_RUN="./lulesh2.0 -s 55 -r 100 -b 0 -c 8 -i 200"
OMPENVVARS="OMP_NUM_THREADS=10 OMP_PLACES=cores OMP_PROC_BIND=close OMP_SCHEDULE=static"

# create a list of all the perf counters we want to run
counters=(
	minor-faults,major-faults
	L1-dcache-load-misses,L1-dcache-loads
	L1-dcache-prefetches,L1-dcache-store-misses
	LLC-load-misses,LLC-loads
	LLC-prefetches,LLC-store-misses
	branch-load-misses,branch-instructions
	dTLB-load-misses,iTLB-load-misses
)

for cntr in "${counters[@]}"
do
	(export ${OMPENVVARS}; perf stat -e $cntr ls)
done