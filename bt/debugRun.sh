#!/bin/bash

SUFFIX="bt-PA-Single-Train"
PROC_BIND="close"
PLACES=cores
WAIT_POL="active"
#APOLLO_PERIOD=10000
APOLLO_PERIOD=1011
THREAD_CAP=36
POLICY="Static,1"
#POLICY="RoundRobin"
#POLICY="Load"
#POLICY="Load,dtree-latest-rank-0-lulesh.cc.apollo.region.l2388.yaml"
#POLICY="Load"
STORE_MODELS=0
STORE_CSVS=0

OMP_NUM_THREADS=$THREAD_CAP \
OMP_WAIT_POLICY=$WAIT_POL \
OMP_PROC_BIND=$PROC_BIND \
OMP_PLACES=$PLACES \
APOLLO_TRACE_CSV_FOLDER_SUFFIX="-$SUFFIX" \
APOLLO_COLLECTIVE_TRAINING=0 \
APOLLO_LOCAL_TRAINING=1 \
APOLLO_RETRAIN_ENABLE=0 \
APOLLO_INIT_MODEL=$POLICY \
APOLLO_STORE_MODELS=$STORE_MODELS \
APOLLO_TRACE_CSV=$STORE_CSVS \
APOLLO_SINGLE_MODEL=1 \
APOLLO_REGION_MODEL=0 \
APOLLO_GLOBAL_TRAIN_PERIOD=$APOLLO_PERIOD \
APOLLO_ENABLE_PERF_CNTRS=1 \
APOLLO_PERF_CNTRS_MLTPX=0 \
APOLLO_DTREE_DEPTH=4 \
APOLLO_PERF_CNTRS="PAPI_DP_OPS,PAPI_TOT_INS" \
APOLLO_SINGLE_MODEL_TO_LOAD="/g/g15/bolet1/workspace/lulesh-region-fix-correct/LULESH/runData/PA_SingleMod_explrRoundRobin_c8_pol3_depth4_trainSize80/dtree-latest-rank-0-lulesh.cc.apollo.region.l2675.yaml" \
srun --partition=pdebug -n1 -N1 --export=ALL ../bin/bt.C.x

APOLLO_SINGLE_MODEL_TO_LOAD="" \

#APOLLO_PERF_CNTRS="PAPI_DP_OPS,PAPI_TOT_INS" \

