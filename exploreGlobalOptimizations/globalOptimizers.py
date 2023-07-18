
import numpy as np
from benchmarks import *
from sko.PSO import PSO
import cma
from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
from bayes_opt.logger import JSONLogger
from bayes_opt.util import load_logs
from bayes_opt.event import Events

# this class will serve as a homogenous interface to all three of the global optimization methods
# that we wish to explore. 

# this is going to use the BO Optimizer for runs
class BOManager:
  def __init__(self, progRegions, seed):
    self.regions = progRegions

    # Range is inclusive, sub 1 from num_region_policies.
    # Add global num_threads policies and per-region policies 
    pbounds = {
      'num_threads': (0, num_threads_policies - 1),
      'places' : (0, num_places_policies - 1),
      'proc_bind' : (0, num_bind_policies - 1)
    }

    # for each region, set the policy index exploration bounds
    for r in self.regions:
      pbounds[r] = (0, num_region_policies - 1)

    # set up the optimizer
    self.opt = BayesianOptimization(
            f=None,
            pbounds = pbounds,
            verbose = 2,
            random_state = seed,
            allow_duplicate_points=True,
    )

    self.utility = UtilityFunction(kind="ucb", kappa=2.5, xi=0.0)

    return

  def registerPoint(self, policy, xtime):
    assert set(list(policy.keys())) == set(self.regions + ['num_threads', 'places', 'proc_bind'])

    # BO does maximization, need to flip the sign on the xtime
    self.opt.register(params=policy, target= (-float(xtime)) )
    return

  def suggestNextPoint(self):
    sugg = self.opt.suggest(self.utility)

    # suggested point is represented with floating point values
    # we round all the values instead
    for k,v in sugg.items():
      sugg[k] = int(np.round(v))

    return sugg


class PSOManager:
	def __init__(self):
		return
		
