import subprocess
import shlex
import argparse
import time
import os, sys
import re
from benchmarks import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

sys.path.append('/usr/WS2/bolet1/apolloDataCollection/skoptSobolAnalysis')
from SACustom import sample_A_B, sample_AB, sobol_indices
from scipy.stats import uniform
from scipy.stats.qmc import scale

# setting the CPU affinity is necessary for properly
# spawning child processes
#print('cpu affinity:', os.sched_getaffinity(0))
os.sched_setaffinity(0, {i for i in range(112)})
#print('NEW cpu affinity:', os.sched_getaffinity(0))

"""
This script will manage launching multiple sbatch jobs to gather sobol
execution data. In particular, sobol requires at most 3*n points of data
to be able to perform the sensitivity analysis. Unfortunately, when dealing
with categorical spaces (as we are), the sobol points to sample can be
repeated and we end up re-sampling points we already have data on. This
script calculates all the sobol points, removes any duplicate points to sample,
then launches the runs to take the samples. This saves us a lot of time
(sometimes 1/3 of the samples -- depending on the space) that we avoid
running and wasting time waiting for.
"""

class SobolSamplesManager:
    def __init__(self, progname, probsize, n, seed, saveDir):
        self.progname = progname
        self.probsize = probsize 
        self.n = n
        self.seed = seed

        # based on the program name and problem size, we know what the lbound and ubound
        # will be, so we calculate them here
        self.d = len(progs[progname][probsize]['region-names'])

        self.lbound = [0]*self.d
        self.ubound = [23]*self.d

        self.samplingDir = saveDir+'/'+progname+'-'+probsize+'_'+str(n)+'points_sobol-seed'+str(seed)

        # make sure the sampling dir exists
        if not os.path.exists(self.samplingDir):
            os.mkdir(self.samplingDir)

        return

    def getSamplingDir(self):
        return self.samplingDir

    def generatePointsToSample(self):
        dists = [uniform(loc=0, scale=1) for i in range(self.d)]
        rng = np.random.default_rng(self.seed)

        A, B = sample_A_B(n=self.n, dists=dists, random_state=rng)
        A = A.T
        B = B.T

        # for the samples, scale them up to the categorical space
        # we use the floor trick from scipy qmc.Sobol.integers
        # to make the samples into a categorical space
        A = scale(A, l_bounds=self.lbound, u_bounds=self.ubound)
        B = scale(B, l_bounds=self.lbound, u_bounds=self.ubound)

        # scipy does flooring for sobol, let's instead do rounding
        #A = np.floor(A).astype(np.int64)
        #B = np.floor(B).astype(np.int64)

        A = np.round(A).astype(np.int64)
        B = np.round(B).astype(np.int64)

        A = A.T
        B = B.T

        # form the AB set from A and B
        AB = sample_AB(A=A, B=B)

        A = A.T
        B = B.T

        # sanity check to make sure everything is OK
        d, d, n = AB.shape
        assert d == self.d
        assert n == self.n

        newAB = np.moveaxis(AB, 0, -1).reshape(d, n*d)
        newAB = newAB.T

        # check for duplicate points in the newAB
        newABuniq = np.unique(newAB, axis=0)
        #assert newABuniq.shape[0] == newAB.shape[0], 'mismatch shape, expected: '+str(newAB.shape[0])+' got: '+str(newABuniq.shape[0])

        # because we can accidentally resample points, let's get all the unique points
        allpts = np.concatenate((A, B, newAB), axis=0)
        print('total points to sample:', allpts.shape)

        assert allpts.shape[0] == (self.n + self.n + self.d*self.n)

        # take only unique points -- these are the points we're going to sample
        # this will be of shape (numpoints, dimension)
        uniq = np.unique(allpts, axis=0)
        print('unique points to sample:', uniq.shape)

        # save the points for later mapping unique points back to the f_A, f_B, and f_AB sets
        self.A = A
        self.B = B
        self.AB = newAB
        self.uniq = uniq

        dfA  = pd.DataFrame(columns=['policy'])
        dfB  = pd.DataFrame(columns=['policy'])
        dfAB = pd.DataFrame(columns=['policy'])

        # convert A, B, and AB into dataframes for lookup
        for rowidx in range(A.shape[0]):
            row = A[rowidx, :]
            row = [str(i) for i in row]
            policy = ','.join(row)
            rowA = {'policy': policy}
            rowA = pd.DataFrame(rowA, index=[0])

            dfA = pd.concat([dfA, rowA], ignore_index=True)

        for rowidx in range(B.shape[0]):
            row = B[rowidx, :]
            row = [str(i) for i in row]
            policy = ','.join(row)
            rowB = {'policy': policy}
            rowB = pd.DataFrame(rowB, index=[0])

            dfB = pd.concat([dfB, rowB], ignore_index=True)

        for rowidx in range(newAB.shape[0]):
            row = newAB[rowidx, :]
            row = [str(i) for i in row]
            policy = ','.join(row)
            rowAB = {'policy': policy}
            rowAB = pd.DataFrame(rowAB, index=[0])

            dfAB = pd.concat([dfAB, rowAB], ignore_index=True)

        self.dfA = dfA 
        self.dfB = dfB 
        self.dfAB = dfAB

        assert dfAB.shape[0] == (self.d * self.n), 'dfAB missing elements...'

        df = pd.DataFrame(columns=['progname', 'probsize', 'policy'])

        # add the unique points to a dataframe
        for rowidx in range(uniq.shape[0]):
            row = uniq[rowidx, :]
            row = [str(i) for i in row]
            policy = ','.join(row)

            newRow = {'progname':self.progname, 'probsize':self.probsize, 'policy':policy}
            newRow = pd.DataFrame(newRow, index=[0])
            df = pd.concat([df, newRow], ignore_index=True)

        assert df.shape[0] == uniq.shape[0]

        df['A'] = df['policy'].map(self.isInA)
        df['B'] = df['policy'].map(self.isInB)
        df['AB'] = df['policy'].map(self.isInAB)

        # let's find the missing points in AB
        noABs = df[df['AB'] == 0]
        for rowidx in range(newAB.shape[0]):
            row = newAB[rowidx, :]
            row = [str(i) for i in row]
            policy = ','.join(row)
            if len(noABs[noABs['policy'] == policy]) != 0:
                print('we found a missing AB!', policy)

        #print(df.head())

        assert df['A'].sum() == self.n
        assert df['B'].sum() == self.n
        #assert df['AB'].sum() == (self.n * self.d), 'got: '+str(df['AB'].sum())+' expected: '+str(self.n * self.d)

        CSVFile = self.samplingDir+'/allUniquePointsToSample.csv'
        df = df.reset_index()

        df.to_csv(CSVFile, columns=['progname', 'probsize', 'policy', 'A', 'B', 'AB'], index=False)
        print('wrote sample points CSV to:', CSVFile)

        self.df = df

        return df

    def isInA(self, policy):
        matched = self.dfA[self.dfA['policy'] == policy]
        return 1 if len(matched) != 0 else 0

    def isInB(self, policy):
        matched = self.dfB[self.dfB['policy'] == policy]
        return 1 if len(matched) != 0 else 0

    def isInAB(self, policy):
        matched = self.dfAB[self.dfAB['policy'] == policy]
        return 1 if len(matched) != 0 else 0


    def readCSVsInDirs(self):

        return

    def getSensitivityFromEvaluations(self, evals):

        # we assume that each elem in evals maps back to uniq



        return


class SobolJobManager:

    def __init__(self, progname, probsize, sobolPoints, rngSeed, outputDir, nodeRuntime, jobsPerNode):
        self.progname = progname
        self.probsize = probsize
        self.sobolPoints = sobolPoints
        self.outputDir = outputDir
        self.nodeRuntime = nodeRuntime
        self.jobsPerNode = jobsPerNode

        self.sobolMan = SobolSamplesManager(progname, probsize, sobolPoints, rngSeed, outputDir)

        self.samplingDir = self.sobolMan.getSamplingDir()
        self.pointsDF = self.sobolMan.generatePointsToSample()

        #print('points head', self.pointsDF.head)

        return


    def setupSobolJobs(self):
        '''
            This will take the pointsDF, split the work up, and create directories with
            a todo.csv file 
        '''

        numJobs = self.pointsDF.shape[0]
        groupIdx = 0
        totalNumGroups = math.ceil(numJobs/self.jobsPerNode)
        self.runDirs = []

        while numJobs > 0:
            todoJobs = self.jobsPerNode if numJobs > self.jobsPerNode else numJobs
            # get the next set of jobs
            startIdx = groupIdx*self.jobsPerNode
            endIdx = startIdx + todoJobs
            jobs = self.pointsDF.iloc[startIdx:endIdx]
            jobs = jobs.reset_index()

            # create a directory for this group
            dirname = self.samplingDir+'/group_'+str(groupIdx)+'_of_'+str(totalNumGroups-1)
            if not os.path.exists(dirname):
                os.mkdir(dirname)

            self.runDirs.append(dirname)

            # create the todo CSV in the group dir, forcing columns
            # since it kept printing index column...
            csvname = dirname+'/todo.csv'
            jobs.to_csv(csvname, columns=['progname', 'probsize', 'policy', 'A', 'B', 'AB'], index=False)

            numJobs -= self.jobsPerNode
            groupIdx += 1

        return

    def launchSobolJobs(self):
        '''
            This will make multiple sbatch script invocations
        '''

        for csvDir in self.runDirs: 
            envvars = {'CSVDIR':csvDir}
            vars_to_use = {**os.environ.copy(), **envvars}

            command = 'sbatch --nodes=1 --time='+self.nodeRuntime+' --output='+csvDir+'/runOutput.log sobolSbatch.sh'
            print('executing command:', command)

            result = subprocess.run(shlex.split(command), env=vars_to_use,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # grab the stdout and errors 
            errors = result.stderr.decode('utf-8')
            output = result.stdout.decode('utf-8')

            print(output)
            print(errors)

        return

# Defining main function
def main():
    parser = argparse.ArgumentParser(description='Sobol Job launcher + analysis script')
    #parser.add_argument('--kernelFnct', help='What scikitlearn kernel to use (with default params)', default='Matern', type=str)

    parser.add_argument('--progName', help='What benchmark should we test with?', default='nas_ft', type=str)
    parser.add_argument('--probSize', help='What benchmark problem size should we test with?', default='medprob', type=str)
    parser.add_argument('--sobolPoints', help='How many sobol points to sample (must be power of 2)', default=16, type=int)
    parser.add_argument('--rngSeed', help='What seed should we use for generation?', required=True, type=int)
    parser.add_argument('--nodeRuntime', help='How long for each node to run in HH:MM:SS format?', required=True, type=str)
    parser.add_argument('--jobsPerNode', help='How many jobs to have per node', default=4, type=int)
    
    args = parser.parse_args()
    print('Got input args:', args)

    SAVE_DIR = EXE_DIR+'/../sobolLogs'

    sobolMan = SobolJobManager(args.progName, args.probSize, args.sobolPoints, 
                               args.rngSeed, SAVE_DIR, args.nodeRuntime, 
                               args.jobsPerNode)
    sobolMan.setupSobolJobs()
    sobolMan.launchSobolJobs()

    #print(sobolMan.pointsDF.head())

    return
  
  
# Using the special variable 
# __name__
if __name__=="__main__":
    main()
