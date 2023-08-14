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

        # check whether the main CSV file already exists, if it matches this shape
        # ignore writing it out
        CSVFile = self.samplingDir+'/allUniquePointsToSample.csv'
        #if (not os.path.isfile(CSVFile)) or ((os.path.isfile(CSVFile)) and (pd.read_csv(CSVFile).shape[0] != self.pointsDF.shape[0])):

        self.pointsDF.to_csv(CSVFile, index=False)
        print('wrote sample points CSV to:', CSVFile)

        # create a unique timestamp for the directory names to avoid overwriting
        self.timestamp = str(int(time.time()))

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
        numJobs = self.todoDF.shape[0]
        totalNumGroups = math.ceil(numJobs/self.jobsPerNode)

        groupIdx = 0

        hparams = list(machines[MACHINE]['envvars'].keys())
        
        toRunDirs = []

        while numJobs > 0:
            todoJobs = self.jobsPerNode if numJobs > self.jobsPerNode else numJobs

            # get the next set of jobs
            startIdx = groupIdx*self.jobsPerNode
            endIdx = startIdx + todoJobs
            jobs = self.todoDF.iloc[startIdx:endIdx]
            jobs = jobs.reset_index()

            # create a directory for this group
            dirname = self.samplingDir+'/job_'+str(groupIdx+1)+'_of_'+str(totalNumGroups)+'-'+self.timestamp
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

    def getIncompleteRuns(self):
        # open up all the directories and concatenate their
        # complete.csv

        # check against the pointsDF to see what's missing

        # setup run dirs to complete missing work

        # job_X_of_Y directories

        # get all the complete.csv files
        completeFiles = list(glob.glob(f'{self.samplingDir}/*/complete.csv'))

        completedData = pd.DataFrame()

        tojoin = []
        # open and concatenate all of them
        for compFile in completeFiles:
            df = pd.read_csv(compFile)
            tojoin += [df]

        completedData = pd.concat([completedData]+tojoin, ignore_index=True)

        #print('completeddata shape', completedData.shape)
        #print('pointsdf shape', self.pointsDF.shape)

        if completedData.shape[0] == 0:
            # if there are no complete files, no runs have been done
            # or if the files were started and nothing written to them
            return self.pointsDF

        # drop any -1 xtimes
        completedData = completedData[completedData['xtime'] != -1.0]

        #print('completeddata shape', completedData.shape)
        #print('pointsdf shape', self.pointsDF.shape)

        # drop the xtime column
        completedData = completedData.drop('xtime', axis=1)
        assert len(list(completedData)) == len(list(self.pointsDF.columns))

        colsToSort = list(self.pointsDF.columns)

        # force the column datatypes to be the same
        self.pointsDF['OMP_NUM_THREADS'] = self.pointsDF['OMP_NUM_THREADS'].astype(completedData.dtypes['OMP_NUM_THREADS'])

        completedData = completedData.sort_values(by=colsToSort).reset_index(drop=True)
        self.pointsDF = self.pointsDF.sort_values(by=colsToSort).reset_index(drop=True)

        #print(completedData.head(), self.pointsDF.head(), sep='\n')
        #print(completedData.tail(), self.pointsDF.tail(), sep='\n')
        #print('completeddata shape', completedData.shape)
        #print('pointsdf shape', self.pointsDF.shape)

        #print(completedData.dtypes, self.pointsDF.dtypes, sep='\n')

        # it's not playing nice with duplicates, let's make a new column of 1s
        # cumsum after groupby to "index" them, then do the isin check
        # drop the extra column after

        self.pointsDF['indic'] = 1
        completedData['indic'] = 1

        self.pointsDF['cumsum'] = self.pointsDF.groupby(colsToSort, as_index=False)['indic'].cumsum().reset_index(drop=True)
        completedData['cumsum'] = completedData.groupby(colsToSort, as_index=False)['indic'].cumsum().reset_index(drop=True)

        completedData = completedData.drop('indic', axis=1)
        self.pointsDF = self.pointsDF.drop('indic', axis=1)

        # let's check against the pointsDF to see what we're missing
        todoRuns = self.pointsDF[~self.pointsDF.apply(tuple,1).isin(completedData.apply(tuple,1))]

        todoRuns = todoRuns.drop('cumsum', axis=1)

        #print('todoruns shape', todoRuns.shape, todoRuns.head())

        todoRuns = todoRuns.reset_index(drop=True)

        return todoRuns


    #def findIncompleteJobs(self):

    #    incompleteRuns = []

    #    # job_X_of_Y directories
    #    dirs = list(os.listdir(self.samplingDir))

    #    for dir in dirs:
    #        dir = self.samplingDir+'/'+dir

    #        if not os.path.isdir(dir):
    #            continue

    #        todoFiles = glob.glob(dir+'/todo.csv')

    #        # this needs to be updated -- if there's no todo.csv file, we can't just launch the run...
    #        # we need to create the todo file...
    #        if len(todoFiles) == 0:
    #            incompleteRuns.append(dir)
    #            continue

    #        else:
    #            todoFile = dir+'/todo.csv'
    #            todo = pd.read_csv(todoFile)
    #            compFile = todoFile.replace('todo', 'complete')

    #            # if some runs were completed
    #            if os.path.isfile(compFile):
    #                comp = pd.read_csv(compFile)

    #                # check that there are no -1 xtimes and the shapes match
    #                comp = comp[comp['xtime'] != -1.0]

    #                # if there are still runs to do, add it to the todo job list
    #                if comp.shape[0] != todo.shape[0]:
    #                    incompleteRuns.append(dir)

    #            else:
    #                incompleteRuns.append(dir)

    #    return incompleteRuns

    def setupJobs(self):
        # this shouldn't really be the trigger, but it will be for now
        #if self.wroteNewPointsFile:
        #    self.runDirs = self.setupAllNewJobs()
        #else:
        #    self.runDirs = self.findIncompleteJobs()
        #    print(self.progname, self.probsize, 'incomplete jobs:', '\n'.join(self.runDirs))
        #return

        self.todoDF = self.getIncompleteRuns()

        print(f'Number of samples left to execute: {self.todoDF.shape[0]}')

        # if there's no work to be done
        if self.todoDF.shape[0] == 0:
            print('no incomplete jobs!')
            self.runDirs = []
        else:
            self.runDirs = self.setupAllNewJobs()
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

        if len(self.runDirs) == 0:
            print('All runs complete, none needed!', self.progname, self.probsize)
            return

        for csvDir in self.runDirs: 

            command = jobRunner+jobNodetime+self.nodeRuntime+' '+jobOutput+csvDir+'/runOutput.log '
            if self.useDebugNodes:
                command += jobDebug

            command += ' jobfile.sh'

            envvars = {'TODO_WORK_DIR':csvDir, 
                       'MOD_LOAD_PYTHON':modloadPy, 
                       'PYTHON_SCRIPT_EXEC_DIR':ROOT_DIR,
                       'CLEAN_FINISH_EXIT_CODE':str(CLEAN_FINISH_EXIT_CODE),
                       'XTIME_LIMIT':str(int(self.nodeRuntime)-3),
                       'PROPAGATE_CMD':command}

            vars_to_use = {**os.environ.copy(), **envvars}

            print(f'executing command: [{command}] \n', '\nwith envvars', envvars)
            print(shlex.split(command))
            result = subprocess.run(shlex.split(command), shell=False, env=vars_to_use,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # grab the stdout and errors 
            errors = result.stderr.decode('utf-8')
            output = result.stdout.decode('utf-8')

            print(output)
            print(errors)

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
