import subprocess
import shlex
import argparse
import time
import os, sys
import re
from benchmarks import *
import numpy as np
import pandas as pd
import math
import glob
from itertools import product
from pathlib import Path

# Need to update this for RUBY later
MAX_ITERATIONS=0
if MACHINE == 'lassen':
    MAX_ITERATIONS = 1188//2
elif MACHINE == 'ruby':
    MAX_ITERATIONS = 1188//2

seeds = [1337, 3827, 9999, 4873]

CLEAN_FINISH_EXIT_CODE=111

# max precision we should round to 
# for avoiding verbose filenames
ROUND_PREC = 3

paramsToSweep = {
    # linspace (start, stop, numPoints)
    'cma':{ 
        'popsize': np.linspace(3,30, 10, endpoint=True).astype(int),
        #'popsize_factor': np.array([1.0]),
        'sigma': np.round(np.linspace(1,30, 10, endpoint=True), ROUND_PREC),
    },
    'pso':{
        'popsize': np.linspace(3,30, 10, endpoint=True).astype(int),
        'w': np.round(np.linspace(0.1, 1, 5, endpoint=True), ROUND_PREC),
        'c1': np.round(np.linspace(0.1, 1.5, 5, endpoint=True), ROUND_PREC),
        'c2': np.round(np.linspace(0.1, 1.5, 5, endpoint=True), ROUND_PREC),
    },
    'bo-ei':{
        'xi': np.round(np.linspace(0.0, 5.0, 100, endpoint=True), ROUND_PREC),
    },
    'bo-poi':{
        'xi': np.round(np.linspace(0.0, 5.0, 100, endpoint=True), ROUND_PREC),
    },
    'bo-ucb':{
        'kappa': np.linspace(2,200, 30, endpoint=True).astype(int),
        'kappa_decay': np.round(np.linspace(0.1, 1.5, 5, endpoint=True), ROUND_PREC),
        'kappa_decay_delay': np.linspace(1,50, 20, endpoint=True).astype(int),
    },
}

def writeTodoFiles(progname, probsize, seed, goMethod, combos, numExecsPerFile, basefilepath):
    basecommand = f'python3 -u --progname={progname} --probsize={probsize} --seed={seed} --maxSteps={MAX_ITERATIONS}'

    if 'bo' in goMethod:
        utilFnct = goMethod.split('-')[1]
        goMethod = 'bo'
        basecommand += f' --optim=bo --utilFnct={utilFnct}'
    else:
        basecommand += f' --optim={goMethod}'

    # combos is assumed to be a list of dicts containing 
    # pytohn args that we will write to the todo file

    numFilesToWrite = int(np.ceil(len(combos)/numExecsPerFile))

    # we assume basefilepath exists
    basefilename = basefilepath+'/'+f'{progname}-{probsize}-{seed}-{goMethod}'

    writtenFiles = []
    currIdx = 0
    for fileIdx in range(numFilesToWrite):
        stopIdx = min((currIdx+numExecsPerFile), len(combos))

        outfilename = basefilename+f'-run_{fileIdx+1}_of_{numFilesToWrite}.sh'

        # create the file and write to it
        shfile = open(outfilename, 'w')

        shfile.write('#!/bin/bash\n\n')

        for combo in combos[currIdx:stopIdx]:
            command = basecommand
            for argname,arg in combo.items():
                command += f' --{argname}={arg}'

            shfile.write(command+'\n')

        shfile.write(f'exit {CLEAN_FINISH_EXIT_CODE}\n')
        shfile.close()
        writtenFiles += [outfilename]
        currIdx += numExecsPerFile
    
    return writtenFiles

def genSweepCombos(goMethod):
    method = paramsToSweep[goMethod]
    combos = []
    for idx,(var,arr) in enumerate(method.items()):
        if idx == 0:
            combos += [ [item] for item in list(arr)]
        else:
            newElems = []
            for combo in combos:
                for item in list(arr):
                    newElems += [ combo+[item] ]
            combos = newElems

    # convert the combos to dicts
    toRet = []
    for combo in combos:
        toRet += [{ var:combo[idx] for idx,var in enumerate(list(method.keys()))}]
    
    return toRet

def genJobs(dbFile, goMethod, maxExecsPerJob=500):
    '''
        Create files in /logs/todoFiles that simply have all the python
        commands for a job to run.
        We have one job running for each GOmethod+seed+progname+probsize combo.
        There is a PROPAGATE_CMD envvar that is executed if the jobfile.sh doesn't
        get to finish its work, it'll relaunch itself till the todo.sh file signals
        completion.
        The work is considered finished when the exit code of 111 is returned by
        the todo.sh script
    '''
    jobfileBasePath = ROOT_DIR+'/logs/todoFiles'

    # setup the jobfile path if it doesn't exist 
    if not os.path.exists(jobfileBasePath):
        os.makedirs(jobfileBasePath)

    prognames = list(progs.keys())
    probsizes = ['smlprob', 'medprob', 'lrgprob']

    modloadPy =  machines[MACHINE]['pythonToModLoad']
    goMethods = list(paramsToSweep.keys())

    # write/generate all the job files
    jobFiles = []

    # generate the values we want to sweep
    combos = genSweepCombos(goMethod)
    print(goMethod, 'num executions to perform ', len(combos))

    for seed in seeds:
        for progname in prognames:
            for probsize in probsizes:
                jobfilename = progname+'-'+probsize+'-'+str(seed)+'-'+goMethod

                files = writeTodoFiles(progname, probsize, seed, goMethod, 
                                       combos, maxExecsPerJob, jobfileBasePath)
                jobFiles += files
                return jobFiles

    print(goMethod, 'num job files', len(jobFiles))
    return jobFiles


def launchJobs(jobsArr, nodeRuntime, useDebugNodes=False):
    '''
        This will make multiple sbatch script invocations.
        We assume that the jobsArr is a list of filenames 
        for the jobfile to execute with.
        nodeRuntime is assumed to be in minutes (at least 3 minutes)
    '''
    jobSys = machines[MACHINE]['jobsystem']
    jobRunner = jobSys['runner']
    jobNodetime = jobSys['nodetime']
    jobOutput = jobSys['output']
    jobDebug = jobSys['debug']

    modloadPy =  machines[MACHINE]['pythonToModLoad']

    runLogsBasePath = ROOT_DIR+'/logs/runLogs'

    # setup the runlon path if it doesn't exist 
    if not os.path.exists(runLogsBasePath):
        os.makedirs(runLogsBasePath)

    # we shave off 3 minutes for the XTIME_LIMIT to 
    # make sure we re-launch the job if lots of work 
    # is still left to do
    baseenvvars = {'MOD_LOAD_PYTHON':modloadPy, 
                   'PYTHON_SCRIPT_EXEC_DIR':ROOT_DIR, 
                   'XTIME_LIMIT':str(nodeRuntime-3)}

    for idx,filename in enumerate(jobsArr):
        vars_to_use = {**os.environ.copy(), **baseenvvars}
        vars_to_use['TODO_WORK_FILE'] = filename

        plainname = Path(filename).stem
        jobOutputLogName = f'{plainname}.out'

        # truncate for bsub restruction of 255 chars in outfile name
        if len(jobOutputLogName) > 251:
            jobOutputLogName = jobOutputLogName[:251]

        jobOutputLog = runLogsBasePath+'/'+jobOutputLogName

        # prepare the command to execute
        command = jobRunner+jobNodetime+str(nodeRuntime)+' '+jobOutput+jobOutputLog+' '

        if useDebugNodes:
            command += jobDebug

        command += 'newJobfile.sh'

        print('executing command:', command, '\nwith envvars', vars_to_use)

        # re-execute this command if the xtime cap gets hit
        vars_to_use['PROPAGATE_CMD'] = command

        result = subprocess.run(command, shell=True, text=True, check=True, 
                                env=vars_to_use, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # grab the stdout
        output = result.stdout

        print(output)

        return

# Defining main function
def main():
    parser = argparse.ArgumentParser(description='Global Optimization Hyperparam Space Exploration Launcher')

    parser.add_argument('--useDebugNodes', help='Should we use debug nodes for testing launches?', default=False, type=bool)
    parser.add_argument('--nodeRuntime', help='How long for each node to run in MINUTES format', required=False, type=int, default=240)
    
    args = parser.parse_args()
    print('Got input args:', args)

    goMethods = list(paramsToSweep.keys())
    
    jobsToLaunch = genJobs('lassen-fullExploreDataset.csv', goMethods[0])


    launchJobs(jobsToLaunch, 5, False)
    #launchJobs(jobsToLaunch, args.nodeRuntime, args.useDebugNodes)
    return
  
  
# Using the special variable 
# __name__
if __name__=="__main__":
    main()
