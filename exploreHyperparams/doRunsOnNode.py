import subprocess
import shlex
import argparse
import time
import re
from benchmarks import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob

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

            # force datatype same-ness
            for k,v in self.todoDF.dtypes.items():
                self.completeDF[k] = self.completeDF[k].astype(v)

            print(self.todoDF.dtypes)
            print(self.completeDF.dtypes)
            print(self.todoDF.head())
            print(self.completeDF.tail())

            # drop any jobs with a -1 xtime, these need to be re-run
            self.completeDF = self.completeDF[self.completeDF['xtime'] != -1.0]

            doneJobs = self.completeDF.drop(columns=['xtime'])

            # remove the completed work items from todoDF
            self.todoDF = self.todoDF[~self.todoDF.isin(doneJobs)]
            self.todoDF = self.todoDF.dropna()

            # force datatype same-ness
            for k,v in self.completeDF.drop(columns=['xtime']).dtypes.items():
                self.todoDF[k] = self.todoDF[k].astype(v)


        else:
            completeCols = ['xtime']+list(self.todoDF.columns)
            self.completeDF = pd.DataFrame(columns = completeCols)
            self.completeCSV = self.todoCSV.replace('todo', 'complete')


        self.envvars = list(self.todoDF.columns)
        self.envvars.remove('progname')
        self.envvars.remove('probsize')

        self.todoDF     = self.todoDF.reset_index(drop=True)
        self.completeDF = self.completeDF.reset_index(drop=True)

        print('Got', self.todoDF.shape[0], 'jobs todo!')
        print('Got', self.completeDF.shape[0], 'jobs pre-completed!')
        print('todo df head:', self.todoDF.head())
        print('Using envvars',self.envvars)
        print('CSVs:', self.todoCSV, self.completeCSV, sep='\n')

        return

    def doJobs(self):
        while self.todoDF.shape[0] != 0:
            # get the next row
            row = self.todoDF.iloc[0]

            progname = row['progname']
            probsize = row['probsize']

            runner = ProgRunner(progname, probsize)

            envvar = row[self.envvars].to_dict()
            
            print('running with envvars:', envvar.items())

            # this is a blocking call
            xtime = runner.runProg(envvar)

            dictToWrite = {'xtime': xtime, 'progname': progname, 'probsize': probsize}
            dictToWrite = {**dictToWrite, **envvar}

            newRow = pd.DataFrame(dictToWrite, index=[0])
            self.completeDF = pd.concat([self.completeDF, newRow], ignore_index=True)
            self.completeDF.to_csv(self.completeCSV, index=False)

            # drop the row from the df
            self.todoDF = self.todoDF.drop(index=0).reset_index(drop=True)

        return



class ProgRunner:

    def __init__(self, progname, probsize):
        self.progname = progname
        self.probsize = probsize

        self.prog = progs[progname]
        self.xtimeRegex = self.prog['xtime-regex']

        self.exe = self.prog['exe'][probsize]

        return

    def extractXtimeFromString(self, toSearch):
        finds = re.findall(self.xtimeRegex, toSearch)

        if len(finds) == 0:
            return -1.0

        # get the last element that the regex found
        xtime = float(finds[-1].rstrip())
        return xtime

    def runProg(self, envvars):

        # make sure all the envvars are strings
        for key in envvars:
            envvars[key] = str(envvars[key])

        vars_to_use = {**os.environ.copy(), **envvars}

        exe_dir = ROOT_DIR+'/../'+self.prog['dirname']+'/buildNoApollo'

        os.chdir(exe_dir)

        command = self.exe

        print('executing command:', command, 'with envvars:', envvars, '\n', end="\t")
        print(shlex.split(command))

        allOutput=''

        toExec = command.split('&&')
        for subcommand in toExec:
            result = subprocess.run(shlex.split(subcommand), shell=True, env=vars_to_use,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # grab the stdout and errors 
            errors = result.stderr.decode('utf-8')
            output = result.stdout.decode('utf-8')

            print(output)
            print(errors)
            allOutput += output


        # extract the xtime from the output
        xtime = self.extractXtimeFromString(allOutput)

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
