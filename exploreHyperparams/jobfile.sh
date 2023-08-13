#!/bin/bash

# this script auto-relaunches the runs if the desired
# exit code is not returned by the doRunsOnNode.py script

module load ${MOD_LOAD_PYTHON}
cd $PYTHON_SCRIPT_EXEC_DIR
echo "Starting execution ${TODO_WORK_DIR}"
pwd
python3 --version


if [[ -z $TODO_WORK_DIR ]]; then
 echo "no work directory specified, terminating"
 exit 1
else
	echo "executing work file -- xtimelimit: $XTIME_LIMIT minutes"
	timeout ${XTIME_LIMIT}m python3 -u ./doRunsOnNode.py --csvDir ${TODO_WORK_DIR}
fi

FINISH_WORK_EXIT_CODE=$?

if [ $FINISH_WORK_EXIT_CODE == $CLEAN_FINISH_EXIT_CODE ]; then
	echo "Work finished, not re-calling script"
else
	# slurm/lsf inherits the calling environemnts envvars, so
	# all the envvars will live on to the next run
	echo "still more work to do, relaunching"
	echo "executing command [$PROPAGATE_CMD]"
	$PROPAGATE_CMD
fi