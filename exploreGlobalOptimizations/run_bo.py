#!/usr/bin/env python3

import subprocess
import os
import csv
import re
import sys
import numpy as np
from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
from bayes_opt.logger import JSONLogger
from bayes_opt.util import load_logs
from bayes_opt.event import Events

def run_program(policies, wait=False):
    num_threads = [160, 80, 40, 20]
    places = ['threads', 'cores', 'sockets']
    bind = [ 'close', 'spread' ]

    env = os.environ.copy()

    places_policy = int(np.round(policies['places']))
    env['OMP_PLACES'] = places[places_policy]

    bind_policy = int(np.round(policies['bind']))
    env['OMP_PROC_BIND'] = str(bind[bind_policy])

    num_threads_policy = int(np.round(policies['num_threads']))
    env['OMP_NUM_THREADS'] = str(num_threads[num_threads_policy])

    policies_str = ','.join([f'{r}={int(np.round(p))}' for r, p in
                     policies.items() if r not in ('num_threads', 'places', 'bind')])
    env['APOLLO_POLICY_MODEL'] = f'StaticRegion,{policies_str}'

    print('env places', env['OMP_PLACES'])
    print('env threads', env['OMP_NUM_THREADS'])
    print('env bind', env['OMP_PROC_BIND'])
    print('env apollo', env['APOLLO_POLICY_MODEL'])
    if wait:
        input('k')

    #cmd = "./lulesh2.0 -s 60 -r 50 -i 10 "
    cmd = "./lulesh2.0 -s 100 -r 100 -b 0 -c 8 -i 20"
    try:
        ps = subprocess.run(cmd, env=env, shell=True, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print('e', e)
        input('ABORT')
        sys.exit(1)

    #print('stdout', ps.stdout)
    #print('stderr', ps.stderr)
    time = re.search('Grind time.* (\d+\.\d+).*overall', ps.stdout).groups(1)[0]
    print('time', time)
    return -float(time)

def main():
    num_region_policies = 15
    num_threads_policies = 4
    num_places_policies = 3
    num_bind_policies = 2
    with open('.apollo/apollo_exec_info.csv', 'r') as f:
        csv_data = csv.DictReader(f, fieldnames=['region', 'execs'])
        regions = [row['region'] for row in csv_data]
    # Range is inclusive, sub 1 from num_region_policies.
    # Add global num_threads policies and per-region policies 
    pbounds = {
            'num_threads': (0, num_threads_policies - 1),
            'places' : (0, num_places_policies - 1),
            'bind' : (0, num_bind_policies - 1)
    }
    for r in regions:
        pbounds[r] = (0, num_region_policies - 1)

    opt = BayesianOptimization(
            f=None,
            pbounds = pbounds,
            verbose = 2,
            random_state = 1337,
    )

    utility = UtilityFunction(kind="ucb", kappa=2.5, xi=0.0)

    # Try to load init static policies or do the experiments.
    try:
        # Load init data.
        load_logs(opt, logs=["./lulesh.json"]);
        print("Optimizer is now aware of {} points.".format(len(opt.space)))
        #print('=== MAX ===')
        #print(opt.max)
        #input('k')
        logger = JSONLogger(path="./lulesh.json", reset=False)
        opt.subscribe(Events.OPTIMIZATION_STEP, logger)
    except FileNotFoundError:
        logger = JSONLogger(path="./lulesh.json", reset=False)
        opt.subscribe(Events.OPTIMIZATION_STEP, logger)
        # Init data file not found, do now.
        print('Init data: ', num_bind_policies * num_places_policies *
                num_threads_policies * num_region_policies)
        for m in range(0, num_bind_policies):
            for k in range(0, num_places_policies):
                for j in range(0, num_threads_policies):
                    for i in range(0, num_region_policies):
                        probe = { 'places' : k, 'num_threads' : j, 'bind' : m }
                        for r in regions:
                            probe[r] = i
                        y = run_program(probe)
                        opt.register(params=probe, target=y)
        #opt.unsubscribe(Events.OPTIMIZATION_STEP, logger)

    # Run BO iters.
    for i in range(100):
        suggested = opt.suggest(utility)
        y = run_program(suggested, False)
        opt.register(params=suggested, target=y)
        print('=== BO iteration:', i, 'x <-',  suggested, '\n y<- ', y)
    print('=== LOG ===')
    for i, res in enumerate(opt.res):
            print("Iteration {}: \n\t{}".format(i, res))
    print('=== MAX ===')
    print(opt.max)

if __name__ == "__main__":
    main()
