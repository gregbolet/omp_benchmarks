#!/usr/bin/env python3

# this program will perform a run of BO, PSO, or CMA for a given benchmark
# we use the database that was generated from the exhaustive OMP hyperparameter
# search to return execution times. This simulated execution approach allows
# us to more quickly sweep over the optimizer hyperparameters to find good
# search settings.

from benchmarks import *
from globalOptimizers import *
import subprocess
import os
import csv
import re
import sys
import argparse
import pandas as pd

# let's just get things working with BO and Lulesh for now

class RunManager:
  def __init__(self, args):
    self.optim = args.optim.lower()
    self.progname = args.progname.lower()
    self.probsize = args.probsize.lower()

    self.step = 0

    if self.probsize not in ['smlprob', 'medprob', 'lrgprob']:
      raise ValueError('Unknown problem size requested', self.probsize)

    if self.progname not in list(progs.keys()):
      raise ValueError('Unknown benchmark requested', self.progname)

    self.prog = progs[self.progname]
    self.xtimeRegex = self.prog['xtime-regex']
    self.dirname = self.prog['dirname']
    self.exe = self.prog['exe'][self.probsize]
    self.regions = self.prog['regions'][self.probsize]
    self.exe_dir = ROOT_DIR+'/../'+self.dirname+'/buildWithApollo'
    self.timeoutSecs = int(self.prog['timeout'][self.probsize])

    if 'bo' in self.optim:
      self.optimizer = BOManager(args.seed, args.utilFnct, args.kappa, 
                                 args.xi, args.kappa_decay, args.kappa_decay_delay)
    elif 'pso' in self.optim:
      pass
    elif 'cma' in self.optim:
      pass
    else:
      raise ValueError('Unknown optimization method requested', optim)
    
    # read in the CSV file with the data to use
    self.db = pd.read_csv(ROOT_DIR+'/databases/'+args.database)

    # get the data for this program and problem size
    self.db = self.db[(self.db['progname'] == self.progname) &
                      (self.db['probsize'] == self.probsize)]

    # map each OMP hyperparameter to some indices
    threads = list(self.db['OMP_NUM_THREADS'].unique())
    threads.sort()
    print('num threads is:', len(threads))
    self.threads_to_index = {thrd:idx for idx,thrd in enumerate(threads)} 
    self.index_to_threads = threads

    procs = list(self.db['OMP_PROC_BIND'].unique())
    procs.sort()
    print('num procs is:', len(procs))
    self.procs_to_index = {proc:idx for idx,proc in enumerate(procs)} 
    self.index_to_procs = procs

    places = list(self.db['OMP_PLACES'].unique())
    places.sort()
    print('num places is:', len(places))
    self.places_to_index = {place:idx for idx,place in enumerate(places)} 
    self.index_to_places = places

    scheds = list(self.db['OMP_SCHEDULE'].unique())
    scheds.sort()
    print('num schedules is:', len(scheds))
    self.sched_to_index = {sched:idx for idx,sched in enumerate(scheds)}
    self.index_to_sched = scheds 

    # setup the logger and log file
    logfilename = self.progname+'-'+self.probsize+'-'+str(self.optimizer)
    self.logger = ExplorationLogger(logfilename)

    return

  # input policy is assumed to already be integers
  def queryDatabase(self, policy):

    #print(policy)

    THREADS_IDX = policy['OMP_NUM_THREADS']
    PROC_IDX = policy['OMP_PROC_BIND']
    PLACES_IDX = policy['OMP_PLACES']
    SCHED_IDX = policy['OMP_SCHEDULE']

    # need to convert the schedule index to a schedule name
    NUM_THREADS = self.index_to_threads[THREADS_IDX]
    PROC_BIND = self.index_to_procs[PROC_IDX]
    PLACES = self.index_to_places[PLACES_IDX]
    SCHEDULE = self.index_to_sched[SCHED_IDX]


    finds = self.db[(self.db['OMP_NUM_THREADS'] == NUM_THREADS) & 
                    (self.db['OMP_PROC_BIND'] == PROC_BIND) &
                    (self.db['OMP_PLACES'] == PLACES) & 
                    (self.db['OMP_SCHEDULE'] == SCHEDULE)]

    #print(finds)
    assert(len(finds) == 1)

    xtime = finds.iloc[0]['xtime']

    print(NUM_THREADS, PROC_BIND, PLACES, SCHEDULE, xtime)

    resultDict = {'step':self.step,
                  'OMP_NUM_THREADS':NUM_THREADS,
                  'OMP_PROC_BIND':PROC_BIND,
                  'OMP_PLACES':PLACES,
                  'OMP_SCHEDULE':SCHEDULE,
                  'xtime': xtime}

    return xtime, resultDict


  def getBestPolicies(self, n=10):
    best = self.db.sort_values(by=['xtime'], ascending=True)
    return best.iloc[:n]

  def getBestFoundPolicies(self, n=10):
    return self.logger.getBestFoundPolicies(n)

  def getExplorationOverhead(self):
    return str(self.optimizer)+': \t'+str(self.optimizer.optimXtime)+' seconds'

  def getEvaluationOverhead(self):
    return str(self.logger.log['xtime'].sum())+' seconds'

  def takeNextStep(self):
    # get the next point to sample and update the model
    policy = self.optimizer.suggestNextPoint()
    xtime, resultDict = self.queryDatabase(policy)

    # pass the evaluation to the logger
    self.logger.logPoint(resultDict)

    self.optimizer.registerPoint(policy, xtime)
    self.step += 1

    return
    
    

def main():
  parser = argparse.ArgumentParser(description='Global Optim Job Runner')

  parser.add_argument('--progname', help='What program to test on', required=False, default='lulesh', type=str)
  parser.add_argument('--probsize', help='What problem size to use', required=False, default='smlprob', type=str)
  parser.add_argument('--database', help='Path to database file', required=False, type=str, default='lassen-fullExploreDataset.csv')

  parser.add_argument('--optim', help='What global optimizer to use', required=False, default='bo', type=str)
  parser.add_argument('--seed', help='What optimizer seed to use for reproducibility', required=False, type=int, default=1337)
  parser.add_argument('--maxSteps', help='How many steps of the algo should we take?', required=False, type=int, default=50)

  # BO-specific arguments
  if '--optim=bo' in sys.argv:
    parser.add_argument('--utilFnct', help='What utility funciton should BO use? (ucb,poi,ei)', required=False, type=str, default='ucb')

    # kappa only used in ucb
    parser.add_argument('--kappa', help='', required=False, type=float, default=2.576)
    parser.add_argument('--kappa_decay', help='>1 boosts exploration, <1 boosts exploitation', required=False, type=float, default=1.0)
    parser.add_argument('--kappa_decay_delay', help='Num iterations to wait before applying kappa decay', required=False, type=int, default=0)

    # xi is only used in poi and ei
    parser.add_argument('--xi', help='', required=False, type=float, default=0.0)


  args = parser.parse_args()
  print('Got input args:', args)

  runMan = RunManager(args)

  step = 0
  while step != args.maxSteps:
    print('step', step, end='\t')
    runMan.takeNextStep()
    step += 1

  print('best database policies')
  print(runMan.getBestPolicies(5))

  print('best found policies')
  print(runMan.getBestFoundPolicies(5))

  print('exploration method overhead', end='\t')
  print(runMan.getExplorationOverhead())

  print('exploration program evaluation overhead', end='\t')
  print(runMan.getEvaluationOverhead())

if __name__ == "__main__":
    main()