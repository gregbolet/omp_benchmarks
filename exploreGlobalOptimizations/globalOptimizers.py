import time
import os
import numpy as np
import random
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
  def __init__(self, logfilename, logfileCols=[]):

    # globalSample and optimXtime are supplied in the resultDict by their respective GO Managers
    self.logfileCols = logfileCols+['OMP_NUM_THREADS', 'OMP_PROC_BIND', 'OMP_PLACES', 
                                    'OMP_SCHEDULE', 'xtime', 'timesSampled', 
                                    'globalSample', 'optimXtime']

    self.log = pd.DataFrame(columns=self.logfileCols)

    self.logfilepath = ROOT_DIR+'/logs/'+logfilename+'.csv'

    # this file path is for once we're done exploring, we save the data to 
    # a file that indicates the exploration was able to complete.
    # We do this so that our batch job script can skip over runs that 
    # are already done (since these are deterministic).
    # There are smarter ways of doing this, but we want results and
    # this is quick to implement.
    self.donelogfilepath = os.path.splitext(self.logfilepath)[0]+'--DONE.csv'

    print('Live-Logging to:', self.logfilepath)

    # create the logfile (overwrite already-existing file)
    self.log.to_csv(self.logfilepath, index=False)

    return

  def logPoint(self, resultDict):
    # check if we've already logged the point we're going to add
    finds = self.log.index[(self.log['OMP_NUM_THREADS'] == resultDict['OMP_NUM_THREADS']) & 
                           (self.log['OMP_PROC_BIND'] == resultDict['OMP_PROC_BIND']) &
                           (self.log['OMP_PLACES'] == resultDict['OMP_PLACES']) & 
                           (self.log['OMP_SCHEDULE'] == resultDict['OMP_SCHEDULE'])].tolist()

    numRepeats = len(finds) + 1

    self.log.loc[finds, 'timesSampled'] = numRepeats

    # flag if it's a repeated sample
    resultDict['timesSampled'] = numRepeats

    # convert the dict to a pandas-friendly format
    resultDict = {k:[v] for k,v in resultDict.items()}
    toAdd = pd.DataFrame.from_dict(resultDict)

    self.log = pd.concat([self.log, toAdd], sort=True, ignore_index=True)

    # write out the CSV file
    self.log.to_csv(self.logfilepath, index=False)
    return

  def getBestFoundPolicies(self, n=10):
    #uniquePts = self.log[self.log['repeatSample'] == 0]
    return self.log.copy(deep=True).sort_values(by=['xtime', 'globalSample'], ascending=True).iloc[:min(n, self.log.shape[0])]

  def getOptimizerXtime(self):
    return self.log['optimXtime'].sum()

  def getExecutionXtime(self):
    return self.log['xtime'].sum()

  def markLogFileAsComplete(self):
    print('Wrote:', self.donelogfilepath)
    self.log.to_csv(self.donelogfilepath, index=False)
    return


class GlobalOptimManager:

  def __init__(self, seed, queryDBFnct, logfilename, logfileCols=[]):
    self.queryDBFnct = queryDBFnct
    self.seed = seed
    self.logfilename = logfilename
    self.logfileCols = logfileCols

    # setup the logger and log file
    self.logger = ExplorationLogger(self.logfilename, self.logfileCols)
    return


# this is going to use the BO Optimizer for runs
class BOManager(GlobalOptimManager):
  def __init__(self, seed, utilFnct, kappa, xi, kappaDecay, 
               kappaDecayDelay, queryDBFnct, logfilename):

    self.utilFnct = utilFnct
    self.kappa = kappa
    self.xi = xi
    self.kappaDecay = kappaDecay
    self.kappaDecayDelay = kappaDecayDelay

    if self.utilFnct == 'ucb':
      logfilename += f'-BO-{self.utilFnct}-k{self.kappa}-kd{self.kappaDecay}-kdd{self.kappaDecayDelay}'
    else:
      logfilename += f'-BO-{self.utilFnct}-xi{self.xi}'

    super().__init__(seed, queryDBFnct, logfilename) 

    # keep track of the global step of the algorithm
    self.globalSample = 0

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

    self.optimXtime = 0

    return

  def __str__(self):
    if self.utilFnct == 'ucb':
      return f'bo-{self.utilFnct}-k{self.kappa}-kd{self.kappaDecay}-kdd{self.kappaDecayDelay}'
    else:
      return f'bo-{self.utilFnct}-xi{self.xi}'


  def takeNextStep(self):

    self.optimXtime = 0

    # get the next point
    start = time.time()
    raw_policy = self.opt.suggest(self.utility)
    self.optimXtime += (time.time() - start)

    # suggested point is represented with floating point values
    # we round all the values instead
    policy = dict()
    for k,v in raw_policy.items():
      policy[k] = int(np.round(v))

    xtime, resultDict = self.queryDBFnct(policy)

    resultDict['globalSample'] = self.globalSample
    resultDict['optimXtime'] = self.optimXtime

    self.logger.logPoint(resultDict)


    # update the model
    self.opt.register(params=raw_policy, target= (-float(xtime)) )

    self.globalSample += 1

    return


# this is used by both PSO and CMA, it keeps track
# of iteration information for logging purposes along
# with the xtime of the optimizer being used
class IterativeFunctionWrapper:
  def __init__(self, f, logger, xtimeHolder):
    self.f = f
    self.logger = logger
    self.iter = 0
    self.sample = 0
    self.pop = 0
    self.globalSample = 0
    self.xtimeHolder = xtimeHolder

  def setPop(self, pop):
    self.pop = pop

  def __call__(self, x):

    # x is a simple array of shape (4,)
    # we preprocess the input array here to pass to the database function
    x = np.round(x).astype(int)

    x_dict = {'OMP_NUM_THREADS':x[0], 'OMP_PROC_BIND':x[1], 'OMP_PLACES':x[2], 'OMP_SCHEDULE':x[3]}
    xtime, resultDict = self.f(x_dict)

    resultDict['globalSample'] = int(self.globalSample)
    resultDict['iter'] = int(self.iter)
    resultDict['sample'] = int(self.sample)

    # calculate the xtime per sample, assumed the same for each sample in one iteration
    resultDict['optimXtime'] = self.xtimeHolder.optimXtime / self.pop

    self.logger.logPoint(resultDict)

    self.globalSample += 1

    self.sample += 1
    if self.sample == self.pop:
      self.iter += 1
      self.sample = 0

    return xtime



class PSOManager(GlobalOptimManager):

  def __init__(self, seed, population, w, c1, c2, queryDBFnct, logfilename):

    # These are the extra columns we're going to be printing to the logfile
    logfileCols = ['iter', 'sample']

    self.pop = population
    self.w = w
    self.c1 = c1
    self.c2 = c2
    self.optimXtime = 0

    logfilename = logfilename+f'-PSO-pop{self.pop}-w{self.w}-c1{self.c1}-c2{self.c2}'

    super().__init__(seed, queryDBFnct, logfilename, logfileCols) 

    # set the global random state seed
    np.random.seed(self.seed)

    self.lower = [0]*4
    self.upper = [float(num_threads_policies-1), float(num_bind_policies-1), 
                  float(num_places_policies-1), float(num_region_policies-1)]

    self.wrapper = IterativeFunctionWrapper(self.queryDBFnct, self.logger, self)

    self.wrapper.setPop(self.pop)

    self.pso = PSO(func=self.wrapper, 
                   n_dim=4, pop=self.pop, lb=self.lower, ub=self.upper, 
                   w=self.w, c1=self.c1, c2=self.c2)

    return
  
  def __str__(self):
    return f'pso-pop{self.pop}-w{self.w}-c1{self.c1}-c2{self.c2}'

  def takeNextStep(self):
    # the following code is equivalent to calling this commented line
    # below, but we added timing instrumentation
    #self.pso.run(max_iter=1)

    self.optimXtime = 0
    start = time.time()
    max_iter=1
    precision = None
    N = 20
    self.pso.max_iter = max_iter or self.pso.max_iter
    c = 0

    for iter_num in range(self.pso.max_iter):
      self.pso.update_V()
      self.pso.recorder()
      self.pso.update_X()
      self.optimXtime += (time.time() - start)
      self.pso.cal_y()
      start = time.time()
      self.pso.update_pbest()
      self.pso.update_gbest()
      if precision is not None:
        tor_iter = np.amax(self.pso.pbest_y) - np.amin(self.pso.pbest_y)
        if tor_iter < precision:
          c = c + 1
          if c > N:
            break
        else:
          c = 0
      if self.pso.verbose:
        print('Iter: {}, Best fit: {} at {}'.format(iter_num, self.pso.gbest_y, self.pso.gbest_x))

      self.pso.gbest_y_hist.append(self.pso.gbest_y)
    self.pso.best_x, self.pso.best_y = self.pso.gbest_x, self.pso.gbest_y
    #return self.pso.best_x, self.pso.best_y






class CMAManager(GlobalOptimManager):

  def __init__(self, seed, sigma, popsize, popsize_factor, queryDBFnct, logfilename):

    # These are the extra columns we're going to be printing to the logfile
    self.sigma = sigma
    self.popsize = popsize
    self.popsize_factor = popsize_factor
    self.optimXtime = 0

    logfilename = logfilename+f'-CMA-sigma{self.sigma}-pop{self.popsize}-popdecay{self.popsize_factor}'

    super().__init__(seed, queryDBFnct, logfilename, []) 

    # set the global random state seed
    np.random.seed(self.seed)
    random.seed(self.seed)

    self.lower = [0]*4
    self.upper = [float(num_threads_policies-1), float(num_bind_policies-1), 
                  float(num_places_policies-1), float(num_region_policies-1)]
    pbounds = [ self.lower, self.upper ]
    x0 = [0]*4

    self.wrapper = IterativeFunctionWrapper(self.queryDBFnct, self.logger, self)

    esOpts = {
              'integer_variables' : list(range(len(x0))),
              'bounds' : pbounds,
              'maxiter' : 100,
              'seed': self.seed,
              'popsize': self.popsize,
              'popsize_factor': self.popsize_factor,
             }

    self.es = cma.CMAEvolutionStrategy(x0, self.sigma, esOpts)

    # use this to print options for future extra hyperparameters
    # self.es.opts.pprint()

    return
  
  def __str__(self):
    return f'-CMA-sigma{self.sigma}-pop{self.popsize}-popdecay{self.popsize_factor}'

  def takeNextStep(self):


    # CMA offers an ask-and-tell interface
    if not self.es.stop():

      self.optimXtime = 0
      start = time.time()

      # these are raw un-rounded requested points
      candidates = self.es.ask()
      self.optimXtime += (time.time() - start)
      
      # solutions contains a list of multiple points to sample
      # this list of points is the "population" which can change
      # over time
      self.wrapper.setPop(len(candidates))

      evaluations = [self.wrapper(point) for point in candidates]
      self.es.tell(candidates, evaluations)
    return
