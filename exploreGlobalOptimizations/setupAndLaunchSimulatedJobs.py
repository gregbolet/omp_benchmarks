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
    MAX_ITERATIONS = 1188//2
elif MACHINE == 'ruby':
    MAX_ITERATIONS = 1188//2

seeds = [1337, 3827, 9999, 4873]

paramsToSweep = {
    # note: max value is excluded if min to max is not evenly divisible by step
    'cma':{ 
        'params':['POPSIZE', 'POPSIZE_FACTOR', 'SIGMA'],
        'min': [3, 1.0, 1],
        'max': [30, 1.0, 30],
        'step': [5, 1.0, 3],
        'runChunkSz':[5,0,0]
    },
    'pso':{
        'params':['POPSIZE', 'W', 'C1', 'C2'],
        'min': [2, 0.1, 0.0, 0.0],
        'max': [30, 1.0, 1.5, 1.5],
        'step': [5, 0.1, 0.15, 0.15],
        'runChunkSz':[3,5,0,0]
    },
    'bo-ei':{
        'params':['XI'],
        'min': [0.0],
        'max': [5.0],
        'step': [0.1],
        'runChunkSz':[0]
    },
    'bo-ucb':{
        'params':['KAPPA', 'KAPPA_DECAY', 'KAPPA_DECAY_DELAY'],
        'min': [2, 0.1, 1],
        'max': [200, 1.5, 50],
        'step': [15, 0.1, 2], # larger kappa gap
        'runChunkSz':[5,0,0]
    },
    'bo-poi':{
        'params':['XI'],
        'min': [0.0],
        'max': [5.0],
        'step': [0.1],
        'runChunkSz':[0]
    },
}

def partitionHyperparams(goMethod):
    '''
        Return a list of dicts with the hyperparams for a particular GO method
    '''
    varSpace = {}
    method = paramsToSweep[goMethod]
    for idx,var in enumerate(method['params']):
        # make the sequences
        minVal = method['min'][idx]
        maxVal = method['max'][idx]
        stepVal = method['step'][idx]
        singleDim = np.arange(minVal, maxVal, stepVal)
        # this is done to match the behavior of seq
        if stepVal == 1.0 and minVal == maxVal:
            singleDim = np.array([minVal])
        elif ((maxVal - minVal) % stepVal) == 0:
            singleDim = np.concatenate(singleDim, np.array([maxVal]))

        # singleDim should keep the sequence that seq would generate
        #print(var, 'singleDim', singleDim)
        varSpace[var] = []
        # now lets partition the array
        chunkSize = method['runChunkSz'][idx]
        if chunkSize == 0:
            varSpace[var] += [singleDim]
        else:
            numChunks = int(np.ceil(len(singleDim)/chunkSize))
            #print(numChunks, len(singleDim), chunkSize)
            for part in range(numChunks):
                startIdx = part*chunkSize
                endIdx = startIdx + chunkSize
                varSpace[var] += [singleDim[startIdx:endIdx]]

    # for each group in the varSpace, let's create all possible combinations with other groups
    #print('varspace to combine:', varSpace)
    combos = []
    for varName, elems in varSpace.items():
        if len(combos) == 0:
            for elem in elems:
                combos += [{varName:elem}]
        else:
            newCombos = []
            for combo in combos:
                for elem in elems:
                    newElem = {}
                    newElem.update(combo)
                    newElem[varName] = elem
                    newCombos += [newElem]
            combos = newCombos

    #print('\n\n combos:', len(combos), combos)
    print(goMethod, 'combos', len(combos))

    return combos

def generateJobs(dbFile, maxIters, goMethod, hyper):
    '''
        Return a list of dicts with envvars to run with
    '''
    jobs = []

    prognames = list(progs.keys())
    probsizes = ['smlprob', 'medprob', 'lrgprob']

    modloadPy =  machines[MACHINE]['pythonToModLoad']

    baseDict = {'DATABASE_FILE':dbFile, 'MAX_ITERATIONS':maxIters, 
                'PYTHON_SCRIPT_EXEC_DIR':ROOT_DIR, 'MOD_LOAD_PYTHON':modloadPy}
    # static database file
    # static max iterations
    # for seed
    # for progname
    # for probsize
    # for partitioned hyperparameters
        # need to extract the start, step, stop from each combo we generated

    # 4 * 6 * 3 = 72 jobs per set of envvars
    for seed in seeds:
        for progname in prognames:
            for probsize in probsizes:
                for config in hyper:
                    envvars = {}
                    envvars.update(baseDict)
                    envvars.update({'RAND_SEED':seed, 'PROGNAME':progname, 'PROBSIZE':probsize})

                    if '-' in goMethod:
                        method,utilFnct = goMethod.split('-')[0],goMethod.split('-')[1]
                        envvars.update({'GO_METHOD':method, 'BO_UTIL_FNCT':utilFnct})
                    else:
                        envvars.update({'GO_METHOD':goMethod})

                    # numpy getting values like 1.4000000000001, need to drop that extra 0000001
                    for varName,vals in config.items():
                        envvars[varName+'_START'] = np.round(np.min(vals),6)
                        envvars[varName+'_STOP'] = np.round(np.max(vals),6)
                        if np.min(vals) == np.max(vals):
                            envvars[varName+'_STEP'] = 1
                        else:
                            envvars[varName+'_STEP'] = np.round(np.max(vals) - np.min(vals), 6)

                    # cast all elements to strings
                    for key,val in envvars.items():
                        envvars[key] = str(val)

                    #print('\n', envvars)
                    jobs += [envvars]

    print(goMethod, 'total number of jobs to submit', len(jobs))

    return jobs

def launchJobs(jobsArr, nodeRuntime, useDebugNodes=False):
    '''
        This will make multiple sbatch script invocations.
        We assume that the jobsArr is a list of dicts that contain
        envvars for execution.
    '''
    jobSys = machines[MACHINE]['jobsystem']
    jobRunner = jobSys['runner']
    jobNodetime = jobSys['nodetime']
    jobOutput = jobSys['output']
    jobDebug = jobSys['debug']

    modloadPy =  machines[MACHINE]['pythonToModLoad']

    for idx, envvars in enumerate(jobsArr): 
        vars_to_use = {**os.environ.copy(), **envvars}

        print(envvars)

        # form a name for the output file
        forName = {'':envvars['PROGNAME']+'-'+envvars['PROBSIZE']+'-'+envvars['GO_METHOD']}
        forName.update(envvars)
        forName.pop('DATABASE_FILE')
        forName.pop('PYTHON_SCRIPT_EXEC_DIR')
        forName.pop('MOD_LOAD_PYTHON')
        forName.pop('MAX_ITERATIONS')
        forName.pop('GO_METHOD')
        forName.pop('RAND_SEED')
        forName.pop('PROGNAME')
        forName.pop('PROBSIZE')

        forName['SEED'] = envvars['RAND_SEED']

        # there's a character limit of 255 chars on the logfile name
        # although the BSUB docs say its 4096...
        # need to cut where we can...
        jobOutputLogName = '-'.join([k.replace('_','')+''+v for k,v in forName.items()])
        print(len(jobOutputLogName)+4)
        #jobOutputLogName = ''.join(['a']*252)

        # forcibly truncate the logfile name to fit the 255 char limit 
        # ('.out' is added to the end, hence 251)
        if len(jobOutputLogName) > 251:
            jobOutputLogName = jobOutputLogName[:251]

        # make the logging path if it doesn't already exist, 
        # this is for SLURM or LSF to write its files to alongside
        loggingdir = ROOT_DIR+'/logs/'+envvars['PROGNAME']+'-'+envvars['PROBSIZE']\
                     +'/'+envvars['GO_METHOD']+'-'+envvars['RAND_SEED']+'/execLogs'

        # set up the logging directory if it doesn't exist
        if not os.path.exists(loggingdir):
            os.makedirs(loggingdir)
            print('made dir', loggingdir)

        command = jobRunner+jobNodetime+str(nodeRuntime)+' '+jobOutput+loggingdir+'/'+jobOutputLogName+'.out '
        if useDebugNodes:
            command += jobDebug

        command += ' jobfile.sh'

        print('executing command:', command, '\nwith envvars', envvars)

        result = subprocess.run(command, shell=True, text=True, check=True, 
                                env=vars_to_use, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # grab the stdout
        output = result.stdout

        print(output)
        #if idx == 3:
        #    return

    return

# Defining main function
def main():
    parser = argparse.ArgumentParser(description='Global Optimization Hyperparam Space Exploration Launcher')

    parser.add_argument('--useDebugNodes', help='Should we use debug nodes for testing launches?', default=False, type=bool)
    parser.add_argument('--nodeRuntime', help='How long for each node to run in MINUTES format', required=False, type=str, default='360')
    
    args = parser.parse_args()
    print('Got input args:', args)

    goMethods = list(paramsToSweep.keys())
    
    jobsToLaunch = []

    for goMethod in goMethods:
        hypers = partitionHyperparams(goMethod)

        jobEnvvars = generateJobs('lassen-fullExploreDataset.csv', MAX_ITERATIONS, goMethod, hypers)
        jobsToLaunch += jobEnvvars
        print(goMethod, len(jobEnvvars))

    print('All jobs to launch', len(jobsToLaunch))

    launchJobs(jobsToLaunch, '60', False)
    #launchJobs(jobsToLaunch, args.nodeRuntime, args.useDebugNodes)
    return
  
  
# Using the special variable 
# __name__
if __name__=="__main__":
    main()
