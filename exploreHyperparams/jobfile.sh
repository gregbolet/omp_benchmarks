#!/bin/bash

module load ${MOD_LOAD_PYTHON}
cd ${PROG_DIR}
echo "Starting execution ${TODO_WORK_DIR}"
pwd
python3 --version
python3 -u ./doRunsOnNode.py --csvDir ${TODO_WORK_DIR}
echo "Execution Completed!"