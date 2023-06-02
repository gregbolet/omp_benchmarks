import subprocess
import shlex
import argparse
import time
import os
import re
from benchmarks import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob

# setting the CPU affinity is necessary for properly
# spawning child processes
print('cpu affinity:', os.sched_getaffinity(0))
os.sched_setaffinity(0, {i for i in range(112)})
print('NEW cpu affinity:', os.sched_getaffinity(0))

class JobRunner:
    def __init__(self, csvDir):
        self.csvDir = csvDir

        self.completeCSV = None
        self.todoCSV = None

        # we expect to find a todoCSV in this dir, get the files
        csvs = list(glob.glob(csvDir + "/*.csv"))

        for csv in csvs:
            if 'todo' in csv:
                self.todoCSV = csv
            elif 'complete' in csv:
                self.completeCSV = csv

        assert self.todoCSV != None

        self.todoDF = pd.read_csv(self.todoCSV)

        if self.completeCSV != None:
            self.completeDF = pd.read_csv(self.completeCSV)

            # remove the completed work items from todoDF
            for index, row in self.completeDF.iterrows():
                row = row[['progname', 'probsize', 'policy']]
                progname = row['progname']
                probsize = row['probsize']
                policy = row['policy']

                self.todoDF = self.todoDF[(self.todoDF['progname'] != progname) &
                                          (self.todoDF['probsize'] != probsize) &
                                          (self.todoDF['policy'] != policy)]

        else:
            completeCols = ['xtime']+list(self.todoDF.columns)
            self.completeDF = pd.DataFrame(columns = completeCols)
            self.completeCSV = self.todoCSV.replace('todo', 'complete')

        print('Got', self.todoDF.shape[0], 'jobs todo!')
        print('Got', self.completeDF.shape[0], 'jobs pre-completed!')
        print('CSVs:', self.todoCSV, self.completeCSV, sep='\n')

        return

    def doJobs(self):
        while self.todoDF.shape[0] != 0:
            # get the next row
            row = self.todoDF.iloc[0]

            progname = row['progname']
            probsize = row['probsize']
            policy = row['policy'].split(',')
            policy = [int(i) for i in policy]
            A = row['A']
            B = row['B']
            AB = row['AB']

            runner = ProgRunner(progname, probsize)
            xtime = runner.runProg(policy)

            dictToWrite = {'xtime': xtime, 'progname': progname, 
                          'probsize': probsize, 'policy':row['policy'],
                          'A':A, 'B':B, 'AB':AB}

            newRow = pd.DataFrame(dictToWrite, index=[0])
            self.completeDF = pd.concat([self.completeDF, newRow], ignore_index=True)
            self.completeDF.to_csv(self.completeCSV, index=False)

            # drop the row from the df
            self.todoDF = self.todoDF.drop(0).reset_index(drop=True)

        return



class ProgRunner:

    def __init__(self, progname, probsize):
        self.progname = progname
        self.probsize = probsize

        self.prog = progs[progname][probsize]
        self.xtimeRegex = progs[progname]['xtime-regex']
        self.regionNames = self.prog['region-names']
        self.exe = self.prog['exe']

        # we'll use this ID to create files/dirs unique to this run
        self.id = str(int(time.time()))
        self.opt_dir = '/tmp/'+self.progname+'-'+self.probsize+'-'+self.id

        # make the directory if it doesn't exist
        if not os.path.exists(self.opt_dir):
            os.mkdir(self.opt_dir) 

        print('Writing opt files to: ', self.opt_dir)

        return

    def writePolicyToRun(self, policyMap):
        '''
            This program will write the APOLLO_OPTIM_READ_DIR envvar
            so that the executing program knows where to read the optimal
            policy from. This will be a dir in the /tmp/ directory since
            it won't suffer from NFS delays when reading during program 
            execution.
            Each region will have a file written in the format of:
            'opt-regionNameGoesHere-rank-0.txt'
            Returns the APOLLO_OPTIM_READ_DIR path to set to the envvar
        '''
        # write each file into the directory
        for name in self.regionNames:
            filename = self.opt_dir+'/opt-'+name+'-rank-0.txt'
            with open(filename, 'w') as outfile:
                policy = str(policyMap[name])
                outfile.write(policy)

        return

    def extractXtimeFromString(self, toSearch):
        finds = re.findall(self.xtimeRegex, toSearch)
        assert len(finds) > 0
        # get the last element that the regex found
        xtime = float(finds[-1].rstrip())
        return xtime


    def setupRun(self, policy):

        policyMap = {}
        regions = self.regionNames

        assert len(regions) == len(policy)

        for idx,region in enumerate(regions):
            policyMap[region] = int(policy[idx])

        self.writePolicyToRun(policyMap)

        # copy the base envvars
        envvars = {key:value for key,value in BASE_APOLLO_ENV_VARS.items()}

        envvars['APOLLO_OPTIM_READ_DIR'] = self.opt_dir

        vars_to_use = {**os.environ.copy(), **envvars}
        return vars_to_use 


    def runProg(self, policy):

        envvars = self.setupRun(policy)

        os.chdir(EXE_DIR)

        command = './'+self.exe

        print('executing command:', command, 'with policy:', policy, end="\t")

        # for some reason (sometimes) when we stdout or stderr to a file, 
        # it sometimes doesn't flush, so we're going to capture
        # the output locally and write it to the logfile ourselves
        result = subprocess.run(shlex.split(command), env=envvars,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # grab the stdout and errors 
        errors = result.stderr.decode('utf-8')
        output = result.stdout.decode('utf-8')

        print(output)
        print(errors)

        assert 'Apollo' in errors

        # extract the xtime from the output
        xtime = self.extractXtimeFromString(output)

        print('\t\textracted xtime:', xtime, 'seconds')

        return xtime

# Defining main function
def main():
    parser = argparse.ArgumentParser(description='Sobol Job Runner')

    parser.add_argument('--csvDir', help='CSV dir with a todo.csv file', required=True, type=str)
    
    args = parser.parse_args()
    print('Got input args:', args)

    runner = JobRunner(args.csvDir)
    runner.doJobs()

    return
  
  
# Using the special variable 
# __name__
if __name__=="__main__":
    main()
