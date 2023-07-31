#!/bin/bash

module load $MOD_LOAD_PYTHON
cd $PYTHON_SCRIPT_EXEC_DIR
echo "Starting execution"
pwd
python3 --version

if [[ -z $TODO_WORK_FILE ]]; then
 echo "no work file specified, terminating"
 exit 1
else
	echo "executing work file -- xtimelimit: $XTIME_LIMIT minutes"
	timeout ${XTIME_LIMIT}m /bin/bash $TODO_WORK_FILE
fi

FINISH_WORK_EXIT_CODE=$?

if (( $FINISH_WORK_EXIT_CODE == 111 )); then
	echo "Work finished, not re-calling script"
else
	# bsub inherits the calling environemnts envvars, so
	# all the envvars will live on to the next run
	echo "still more work to do, relaunching"
	echo "executing command [$PROPAGATE_CMD]"
	$PROPAGATE_CMD
fi