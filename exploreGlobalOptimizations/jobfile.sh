#!/bin/bash

module load ${MOD_LOAD_PYTHON}
cd ${PYTHON_SCRIPT_EXEC_DIR}
echo "Starting execution ${TODO_WORK_DIR}"
pwd
python3 --version

#GO_METHOD
#RAND_SEED
#MAX_ITERATIONS
#PROGNAME
#PROBSIZE
#DATABASE_PATH
echo "Using global exploration method ${GO_METHOD}"

# this script assumes that for the given GO method, we have an array
# of values that will be tested with and cycled through

if [ $GO_METHOD = 'bo' ]; then
	echo "using bo"
	if [ $BO_UTIL_FNCT = 'ucb' ]; then
		# KAPPA_START, KAPPA_STOP, KAPPA_STEP
		# KAPPA_DECAY_START, KAPPA_DECAY_STOP, KAPPA_DECAY_STEP
		# KAPPA_DECAY_DELAY_START, KAPPA_DECAY_DELAY_STOP, KAPPA_DECAY_DELAY_STEP
		echo "using ucb"


	elif [ $BO_UTIL_FNCT = 'poi' ]; then
		# XI_START, XI_STOP, XI_STEP
		echo "using poi"

	elif [ $BO_UTIL_FNCT = 'ei' ]; then
		# XI_START, XI_STOP, XI_STEP
		echo "using ei"

	else
		echo "no BO_UTIL_FNCT specified"

	fi

elif [ $GO_METHOD = 'pso' ]; then

elif [ $GO_METHOD = 'cma' ]; then

else
	echo "No GO_METHOD specified, exiting..."
fi


#if pso
# POPSIZE_ARRAY
# W_ARRAY
# C1_ARRAY
# C2_ARRAY

#if cma
# POPSIZE_ARRAY
# POPSIZE_FACTOR_ARRAY
# SIGMA_ARRAY

python3 -u ./doRunsOnNode.py --csvDir ${TODO_WORK_DIR}
echo "Execution Completed!"