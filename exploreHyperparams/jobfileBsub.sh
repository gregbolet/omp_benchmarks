#!/bin/bash

source ~/workspace/py3.10.8-gregvirtenv/bin/activate
cd /g/g15/bolet1/workspace/apolloDataCollection/skoptSobolAnalysis
echo "Starting execution ${CSVDIR}"
pwd
python --version
python -u ./doSobolJob.py --csvDir ${CSVDIR}
echo "Execution Completed!"