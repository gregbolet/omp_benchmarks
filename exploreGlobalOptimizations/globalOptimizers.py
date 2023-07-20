import time
import os
import numpy as np
import pandas as pd
from benchmarks import *
from sko.PSO import PSO
import cma
from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
from bayes_opt.logger import JSONLogger
from bayes_opt.util import load_logs
from bayes_opt.event import Events

class ExplorationLogger:
  def __init__(self, logfilename):
    self.log = pd.DataFrame(columns=['step', 'OMP_NUM_THREADS', 'OMP_PROC_BIND', 'OMP_PLACES', 'OMP_SCHEDULE', 'xtime'])

    self.logfilepath = ROOT_DIR+'/logs/'+logfilename+'.csv'

    # create the logfile
    self.log.to_csv(self.logfilepath, index=False)

    return

  def logPoint(self, resultDict):

    resultDict = {k:[v] for k,v in resultDict.items()}
    self.log = pd.concat([self.log, pd.DataFrame.from_dict(resultDict)], ignore_index=True)

    # write out the CSV file
    self.log.to_csv(self.logfilepath, index=False)
    return

  def getBestFoundPolicies(self, n=10):
    return self.log.sort_values(by=['xtime', 'step'], ascending=True).iloc[:min(n, self.log.shape[0])]

# this is going to use the BO Optimizer for runs
class BOManager:
  def __init__(self, seed, utilFnct, kappa, xi, kappaDecay, kappaDecayDelay):

    self.utilFnct = utilFnct
    self.kappa = kappa
    self.xi = xi
    self.kappaDecay = kappaDecay
    self.kappaDecayDelay = kappaDecayDelay

    # keep track of the total time consumed by calling BO functions
    self.optimXtime = 0.0

    # set the global random state seed
    np.random.seed(seed)

    # Range is inclusive, sub 1 from num_region_policies.
    pbounds = {
      'OMP_NUM_THREADS': (0, num_threads_policies - 1),
      'OMP_PROC_BIND' : (0, num_bind_policies - 1),
      'OMP_PLACES' : (0, num_places_policies - 1),
      'OMP_SCHEDULE' : (0, num_region_policies - 1)
    }

    # set up the optimizer
    start = time.time()
    self.opt = BayesianOptimization(
            f=None,
            pbounds = pbounds,
            verbose = 2,
            random_state = seed,
            allow_duplicate_points=True,
    )

    self.utility = UtilityFunction(kind=utilFnct, kappa=kappa, xi=xi, 
                                   kappa_decay=kappaDecay, 
                                   kappa_decay_delay=kappaDecayDelay)

    self.optimXtime = self.optimXtime + (time.time() - start)
    return

  def __str__(self):
    if self.utilFnct == 'ucb':
      return f'bo-{self.utilFnct}-k{self.kappa}-kd{self.kappaDecay}-kdd{self.kappaDecayDelay}'
    else:
      return f'bo-{self.utilFnct}-xi{self.xi}'


  def registerPoint(self, policy, xtime):
    # BO does maximization, need to flip the sign on the xtime
    start = time.time()
    self.opt.register(params=policy, target= (-float(xtime)) )
    self.optimXtime = self.optimXtime + (time.time() - start)
    return

  def suggestNextPoint(self):
    start = time.time()
    sugg = self.opt.suggest(self.utility)
    self.optimXtime = self.optimXtime + (time.time() - start)

    # suggested point is represented with floating point values
    # we round all the values instead
    for k,v in sugg.items():
      sugg[k] = int(np.round(v))

    return sugg


class PSOManager(PSO):
  def __init__(self, progRegions, seed, population):
    # set the global random state seed
    np.random.seed(seed)
    self.regions = progRegions


    lower = [0]*(3 + len(self.regions))
    upper = [num_threads_policies-1e-3, num_bind_policies-1e-3, num_places_policies-1e-3] + [num_region_policies-1e-3]*(len(self.regions))

    super().__init__(func=(lambda x: 0), n_dim=len(self.regions)+3, pop=population, 
                     lb=lower, ub=upper, w=0.8, c1=0.5, c2=0.5)

    self.iter = 0

    # perform part of the first iteration
    self.update_V()
    self.recorder()
    self.update_X()

    # create a buffer of the next set of points/particles to sample



    return

  def registerPoint(self, policy, xtime):
    return

  def suggestNextPoint(self):
    return

