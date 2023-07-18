#!/usr/bin/env python3

# this program will perform a run of BO, PSO, or CMA for a given benchmark

from benchmarks import *
from globalOptimizers import *
import subprocess
import os
import csv
import re
import sys
import argparse

# let's just get things working with BO and Lulesh for now

class RunManager:
  def __init__(self, optim, progname, probsize, seed):
    self.optim = optim.lower()
    self.progname = progname.lower()
    self.probsize = probsize.lower()

    if self.probsize not in ['smlprob', 'medprob', 'lrgprob']:
      raise ValueError('Unknown problem size requested', probsize, self.probsize)

    if self.progname not in list(progs.keys()):
      raise ValueError('Unknown benchmark requested', progname, self.progname)

    self.prog = progs[progname]
    self.xtimeRegex = self.prog['xtime-regex']
    self.dirname = self.prog['dirname']
    self.exe = self.prog['exe'][self.probsize]
    self.regions = self.prog['regions'][self.probsize]
    self.exe_dir = ROOT_DIR+'/../'+self.dirname+'/buildWithApollo'
    self.timeoutSecs = int(self.prog['timeout'][self.probsize])

    if 'bo' in self.optim:
      self.optimizer = BOManager(self.regions, seed)
    elif 'pso' in self.optim:
      pass
    elif 'cma' in self.optim:
      pass
    else:
      raise ValueError('Unknown optimization method requested', optim)
    
    return

  def extractXtimeFromString(self, toSearch):
    finds = re.findall(self.xtimeRegex, toSearch)

    if len(finds) == 0:
        return -1.0

    # get the last element that the regex found
    xtime = float(finds[-1].rstrip())
    return xtime

  # input policy is assumed to already be integers
  def runProgram(self, policy):
    env = os.environ.copy()

    env['OMP_PLACES'] = str(places[policy['places']])
    env['OMP_PROC_BIND'] = str(proc_bind[policy['proc_bind']])
    env['OMP_NUM_THREADS'] = str(num_threads[policy['num_threads']])

    policies_str = ','.join([f'{r}={p}' for r, p in 
                    policy.items() if r not in ('num_threads', 'places', 'proc_bind')])

    env['APOLLO_POLICY_MODEL'] = f'StaticRegion,{policies_str}'
    
    print('env places:', env['OMP_PLACES'])
    print('env num_threads:', env['OMP_NUM_THREADS'])
    print('env proc_bind:', env['OMP_PROC_BIND'])
    print('env apollo:', env['APOLLO_POLICY_MODEL'])

    os.chdir(self.exe_dir)

    command = self.exe

    print('executing command:', command)

    allOutput=''
    timeoutError = False

    toExec = command.split('&&')
    for subcommand in toExec:
      result = ''
      try:
        result = subprocess.run(subcommand, shell=True, text=True, check=True, 
                                env=env, timeout=self.timeoutSecs,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        print(result.stdout)
        allOutput += result.stdout

      except subprocess.TimeoutExpired:
        print(self.progname, self.probsize, 'REACHED MAX EXECUTION TIME -- Killed after:', self.timeoutSecs, 'seconds')
        timeoutError = True
      except subprocess.CalledProcessError as e:
        print('Execution Error - Process exited with non-zero exit code', e)
        sys.exit(1)

    # extract the xtime from the output
    if timeoutError:
      return float(self.timeoutSecs)
    else:
      xtime = self.extractXtimeFromString(allOutput)
      print('\t\textracted xtime:', xtime, 'seconds')
      return xtime


  def takeNextStep(self):
    # get the next point to sample and update the model
    policy = self.optimizer.suggestNextPoint()
    xtime = self.runProgram(policy)

    if xtime == -1.0:
      raise ValueError(self.progname, self.probsize, '\t Could not extract xtime from execution results')

    self.optimizer.registerPoint(policy, xtime)
    print('Got a new point! ', policy, xtime)
    return
    
    

def main():
  parser = argparse.ArgumentParser(description='Global Optim Job Runner')

  parser.add_argument('--optim', help='What global optimizer to use', required=True, default='bo', type=str)
  parser.add_argument('--progname', help='What program to test on', required=True, default='lulesh', type=str)
  parser.add_argument('--probsize', help='What problem size to use', required=True, default='smlprob', type=str)
  parser.add_argument('--seed', help='What optimizer seed to use for reproducibility', required=False, type=int, default=1337)
  parser.add_argument('--maxSteps', help='How many steps of the algo should we take?', required=False, type=int, default=10)

  args = parser.parse_args()
  print('Got input args:', args)

  runMan = RunManager(args.optim, args.progname, args.probsize, args.seed)

  step = 0
  while step != args.maxSteps:
    runMan.takeNextStep()
    step += 1

if __name__ == "__main__":
    main()