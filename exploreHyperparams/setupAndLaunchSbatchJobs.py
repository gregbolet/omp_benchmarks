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


# generate the samples we want to take
class SamplesManager:
    def __init__(self, progname, probsize):
        self.progname = progname
        self.probsize = probsize
        return

    def generatePointsToSample(self):
        envvars = machines[MACHINE]['envvars']

        # let's make all the combinations of envvars
        toexpand = list(envvars.values())
        combos = list(product(*toexpand))
        #print(len(combos))

        # based on the machine, make the columns of hyperparameters
        hparams = list(envvars.keys())
        cols = ['progname', 'probsize'] + hparams
        df = pd.DataFrame(columns=cols)
        #print(df.columns)

        # now populate the dataframe
        for combo in combos:
            vals = [self.progname, self.probsize]+list(combo)
            toappend = pd.DataFrame([dict(zip(cols, vals))])
            df = pd.concat([df, toappend], ignore_index=True)

        df = df.reset_index()
        #print(df.shape)
        #print(df.head())
        #print(df.tail())

        return df

class JobManager:

    def __init__(self, progname, probsize, nodeRuntime, jobsPerNode, numTrials, useDebugNodes):
        self.progname = progname
        self.probsize = probsize
        self.nodeRuntime = nodeRuntime
        self.jobsPerNode = jobsPerNode
        self.numTrials = numTrials
        self.useDebugNodes = useDebugNodes
        self.runDirs = []

        self.samplingDir = ROOT_DIR+'/explorData/'+progname+'-'+probsize

        #print('sampling dir', self.samplingDir)

        # check that the dir exists, if not, create it
        if not os.path.exists(self.samplingDir):
            os.mkdir(self.samplingDir)

        self.samplMan = SamplesManager(progname, probsize)
        self.uniquePointsDF = self.samplMan.generatePointsToSample()

        self.pointsDF = self.setupSamplingFile()

        self.wroteNewPointsFile = False

        # check whether the main CSV file already exists, if it matches this shape
        # ignore writing it out
        CSVFile = self.samplingDir+'/allUniquePointsToSample.csv'
        if (os.path.isfile(CSVFile)) and (pd.read_csv(CSVFile).shape[0] != self.pointsDF.shape[0]):
            self.pointsDF.to_csv(CSVFile, index=False)
            print('wrote sample points CSV to:', CSVFile)
            self.wroteNewPointsFile = True

        return

    def setupSamplingFile(self):

        df = self.uniquePointsDF.copy(deep=True)

        # let's make a new df with the repeated trials
        for i in range(self.numTrials-1):
            df = pd.concat([df, self.uniquePointsDF], ignore_index=True)

        hparams = list(machines[MACHINE]['envvars'].keys())
        df = df.sort_values(by=hparams)
        df = df.reset_index()

        df = df[['progname', 'probsize']+hparams]

        return df

    def setupAllNewJobs(self):
        numJobs = self.pointsDF.shape[0]
        totalNumGroups = math.ceil(numJobs/self.jobsPerNode)

        groupIdx = 0

        hparams = list(machines[MACHINE]['envvars'].keys())
        
        toRunDirs = []

        while numJobs > 0:
            todoJobs = self.jobsPerNode if numJobs > self.jobsPerNode else numJobs

            # get the next set of jobs
            startIdx = groupIdx*self.jobsPerNode
            endIdx = startIdx + todoJobs
            jobs = self.pointsDF.iloc[startIdx:endIdx]
            jobs = jobs.reset_index()

            # create a directory for this group
            dirname = self.samplingDir+'/job_'+str(groupIdx+1)+'_of_'+str(totalNumGroups)
            if not os.path.exists(dirname):
                os.mkdir(dirname)

            toRunDirs.append(dirname)

            jobs = jobs[['progname', 'probsize']+hparams]
            # create the todo CSV in the group dir
            csvname = dirname+'/todo.csv'
            jobs.to_csv(csvname, index=False)

            numJobs -= self.jobsPerNode
            groupIdx += 1

        return toRunDirs

    def findIncompleteJobs(self):

        incompleteRuns = []

        # job_X_of_Y directories
        dirs = list(os.listdir(self.samplingDir))

        for dir in dirs:
            dir = self.samplingDir+'/'+dir

            if not os.path.isdir(dir):
                continue

            todoFiles = glob.glob(dir+'/todo.csv')

            if len(todoFiles) == 0:
                incompleteRuns.append(dir)
                continue

            else:
                todoFile = dir+'/todo.csv'
                todo = pd.read_csv(todoFile)
                compFile = todoFile.replace('todo', 'complete')

                # if some runs were completed
                if os.path.isfile(compFile):
                    comp = pd.read_csv(compFile)

                    # check that there are no -1 xtimes and the shapes match
                    comp = comp[comp['xtime'] != -1.0]

                    # if there are still runs to do, add it to the todo job list
                    if comp.shape[0] != todo.shape[0]:
                        incompleteRuns.append(dir)

                else:
                    incompleteRuns.append(dir)

        return incompleteRuns

    def setupJobs(self):
        # this shouldn't really be the trigger, but it will be for now
        if self.wroteNewPointsFile:
            self.runDirs = self.setupAllNewJobs()
        else:
            self.runDirs = self.findIncompleteJobs()
            print(self.progname, self.probsize, 'incomplete jobs:', '\n'.join(self.runDirs))
        return

    def launchJobs(self):
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
    parser = argparse.ArgumentParser(description='OMP Hyperparam Space Exploration Launcher')

    parser.add_argument('--progName', help='What benchmark should we test with?', default='bt_nas', type=str)
    parser.add_argument('--probSize', help='What problem size should we test with?', default='medprob', type=str)
    parser.add_argument('--numTrials', help='How many repeat trials should we do?', default=2, type=int)
    parser.add_argument('--jobsPerNode', help='How many jobs to have per node', default=100, type=int)
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
