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

# Need to update this for RUBY later
MAX_ITERATIONS=0
if MACHINE == 'lassen':
    MAX_ITERATIONS = 1350
elif MACHINE == 'ruby':
    MAX_ITERATIONS = 1350

paramsToSweep = {
    # 40 * 15 * 25 = 15,000
    'bo-ucb':{
        'params':['KAPPA', 'KAPPA_DECAY', 'KAPPA_DECAY_DELAY'],
        'min': [2, 0.1, 1],
        'max': [200, 1.5, 50],
        'step': [5, 0.1, 2]
    },
    # 51 combinations to try
    'bo-poi':{
        'params':['XI'],
        'min': [0.0],
        'max': [5.0],
        'step': [0.1]
    },
    # 51 combinations to try
    'bo-ei':{
        'params':['XI'],
        'min': [0.0],
        'max': [5.0],
        'step': [0.1]
    },
    # PSO: 15 * 10 * 11 * 11 = 18,150 combinations to try
    'pso':{
        'params':['POPSIZE', 'W', 'C1', 'C2'],
        'min': [1, 0.1, 0.0, 0.0],
        'max': [30, 1.0, 1.5, 1.5],
        'step': [2, 0.1, 0.15, 0.15]
    },
    # CMA: 15 * 15 * 15 = 3375 combinations to try
    'cma':{ 
        'params':['POPSIZE', 'POPSIZE_FACTOR', 'SIGMA'],
        'min': [1, 0.1, 1],
        'max': [30, 1.5, 30],
        'step': [2, 0.1, 2]
    }
}


def launchJobs():
    '''
        This will make multiple sbatch script invocations
    '''
    jobSys = machines[MACHINE]['jobsystem']
    jobRunner = jobSys['runner']
    jobNodetime = jobSys['nodetime']
    jobOutput = jobSys['output']
    jobDebug = jobSys['debug']

    modloadPy =  machines[MACHINE]['pythonToModLoad']

    for csvDir in self.runDirs: 
        envvars = {'TODO_WORK_DIR':csvDir, 'MOD_LOAD_PYTHON':modloadPy, 'PROG_DIR':ROOT_DIR}
        vars_to_use = {**os.environ.copy(), **envvars}

        command = jobRunner+jobNodetime+self.nodeRuntime+' '+jobOutput+csvDir+'/runOutput.log '
        if self.useDebugNodes:
            command += jobDebug

        command += ' jobfile.sh'
        #comand = '"'+command+'"'

        print('executing command:', command, '\nwith envvars', envvars)
        print(shlex.split(command))
        result = subprocess.run(shlex.split(command), shell=False, env=vars_to_use,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # grab the stdout and errors 
        errors = result.stderr.decode('utf-8')
        output = result.stdout.decode('utf-8')

        print(output)
        print(errors)


    if len(self.runDirs) == 0:
        print('All runs complete, none needed!', self.progname, self.probsize)

    return

# Defining main function
def main():
    parser = argparse.ArgumentParser(description='Global Optimization Hyperparam Space Exploration Launcher')

    parser.add_argument('--useDebugNodes', help='Should we use debug nodes for testing launches?', default=False, type=bool)
    parser.add_argument('--nodeRuntime', help='How long for each node to run in MINUTES format', required=True, type=str)
    
    args = parser.parse_args()
    print('Got input args:', args)

    jobMan = JobManager(args.progName, args.probSize, args.nodeRuntime, 
                          args.jobsPerNode, args.numTrials, args.useDebugNodes)
    jobMan.setupJobs()
    jobMan.launchJobs()

    return
  
  
# Using the special variable 
# __name__
if __name__=="__main__":
    main()
