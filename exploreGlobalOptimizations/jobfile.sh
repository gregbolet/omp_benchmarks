#!/bin/bash

module load ${MOD_LOAD_PYTHON}
cd ${PYTHON_SCRIPT_EXEC_DIR}
echo "Starting execution"
pwd
python3 --version

#DATABASE_FILE
#MAX_ITERATIONS

#RAND_SEED
#PROGNAME
#PROBSIZE
#GO_METHOD

BASE_COMMAND="python3 -u simulateGlobalOptimRunOnNode.py --progname=$PROGNAME --probsize=$PROBSIZE"
BASE_COMMAND+=" --database=$DATABASE_FILE --optim=$GO_METHOD --seed=$RAND_SEED"
BASE_COMMAND+=" --maxSteps=$MAX_ITERATIONS"

echo "executing with the following base command: [$BASE_COMMAND]"

if [ $GO_METHOD = 'bo' ]; then
	echo "using bo with $BO_UTIL_FNCT"
	if [ $BO_UTIL_FNCT = 'ucb' ]; then
		# KAPPA_START, KAPPA_STOP, KAPPA_STEP
		# KAPPA_DECAY_START, KAPPA_DECAY_STOP, KAPPA_DECAY_STEP
		# KAPPA_DECAY_DELAY_START, KAPPA_DECAY_DELAY_STOP, KAPPA_DECAY_DELAY_STEP
		for kappa in $(seq $KAPPA_START $KAPPA_STEP $KAPPA_STOP)
		do
			for kappa_decay in $(seq $KAPPA_DECAY_START $KAPPA_DECAY_STEP $KAPPA_DECAY_STOP)
			do
				for kappa_decay_delay in $(seq $KAPPA_DECAY_DELAY_START $KAPPA_DECAY_DELAY_STEP $KAPPA_DECAY_DELAY_STOP)
				do
					TO_EXEC="$BASE_COMMAND --utilFnct=$BO_UTIL_FNCT"
					TO_EXEC+=" --kappa=$kappa --kappa_decay=$kappa_decay --kappa_decay_delay=${kappa_decay_delay}"

					echo "Executing command: [$TO_EXEC]"
					$( $TO_EXEC )
				done
			done
		done



	elif [ $BO_UTIL_FNCT = 'poi' ] || [ $BO_UTIL_FNCT = 'ei' ]; then
		# XI_START, XI_STOP, XI_STEP
		for xi in $(seq $XI_START $XI_STEP $XI_STOP)
		do
			TO_EXEC="$BASE_COMMAND --utilFnct=$BO_UTIL_FNCT"
			TO_EXEC+=" --xi=$xi"

			echo $TO_EXEC
			$( $TO_EXEC )
		done

	else
		echo "no BO_UTIL_FNCT specified"
	fi

elif [ $GO_METHOD = 'pso' ]; then
	# POPSIZE_START POPSIZE_STEP POPSIZE_STOP
	# W_START W_STEP W_STOP
	# C1_START C1_STEP C1_STOP
	# C2_START C2_STEP C2_STOP
	for popsize in $(seq $POPSIZE_START $POPSIZE_STEP $POPSIZE_STOP)
	do
		for w in $(seq $W_START $W_STEP $W_STOP)
		do
			for c1 in $(seq $C1_START $C1_STEP $C1_STOP)
			do
				for c2 in $(seq $C2_START $C2_STEP $C2_STOP)
				do
					TO_EXEC="$BASE_COMMAND --popsize=$popsize"
					TO_EXEC+=" --w=$w --c1=$c1 --c2=$c2"

					echo $TO_EXEC
					$( $TO_EXEC )
				done
			done
		done
	done

elif [ $GO_METHOD = 'cma' ]; then
	# POPSIZE_START POPSIZE_STEP POPSIZE_STOP 
	# POPSIZE_FACTOR_START POPSIZE_FACTOR_STEP POPSIZE_FACTOR_STOP
	# SIGMA_START SIGMA_STEP SIGMA_STOP
	for popsize in $(seq $POPSIZE_START $POPSIZE_STEP $POPSIZE_STOP)
	do
		for popsize_factor in $(seq $POPSIZE_FACTOR_START $POPSIZE_FACTOR_STEP $POPSIZE_FACTOR_STOP)
		do
			for sigma in $(seq $SIGMA_START $SIGMA_STEP $SIGMA_STOP)
			do
				TO_EXEC="$BASE_COMMAND --popsize=$popsize"
				TO_EXEC+=" --popsize_factor=$popsize_factor --sigma=$sigma"

				echo $TO_EXEC
				$( $TO_EXEC )
			done
		done
	done

else
	echo "No GO_METHOD specified, exiting..."
fi