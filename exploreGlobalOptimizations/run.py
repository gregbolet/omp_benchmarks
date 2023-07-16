#!/usr/bin/env python3

import subprocess
import os
import csv
import re
import sys
#from bayes_opt import BayesianOptimization
from skopt import Optimizer
from skopt.space import Integer, Categorical
from skopt import dump, load

def run_program(policies, regions):
    num_threads = [160, 80, 40, 20]
    regions_policies = zip(regions, policies[1:])
    env = os.environ.copy()
    policies_str = ','.join([f'{r}={p}' for r, p in regions_policies])
    env['APOLLO_POLICY_MODEL'] = f'StaticRegion,{policies_str}'
    env['OMP_PLACES'] = 'threads'
    env['OMP_NUM_THREADS'] = str(num_threads[policies[0]])
    print('env places', env['OMP_PLACES'])
    print('env threads', env['OMP_NUM_THREADS'])
    print('env apollo', env['APOLLO_POLICY_MODEL'])
    cmd = "./lulesh2.0 -s 60 -r 50 -i 10 "
    #cmd = "./lulesh2.0 -s 55 -r 100 -b 0 -c 8 -i 20"
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
    return float(time)

def main():
    num_region_policies = 30
    num_global_policies = 4
    with open('.apollo/apollo_exec_info.csv', 'r') as f:
        csv_data = csv.DictReader(f, fieldnames=['region', 'execs'])
        regions = [row['region'] for row in csv_data]
    # Range is inclusive, sub 1 from num_region_policies.
    # Add global policies for num_threads and per-region policies 
    space = [Integer(0, num_global_policies-1)] + [Integer(0, num_region_policies-1)]*len(regions)
    opt = Optimizer(space, n_initial_points=0, random_state= 1337)

    # Try to load init static policies or do the experiments.
    try:
        res = load('lulesh.pkl')
        # Load init data.
        for x,y in zip(res.x_iters, res.func_vals):
            print('tell', x, '->', y)
            opt.tell(x, y)
    except FileNotFoundError:
        # Init data file not found, do now.
        for j in range(0, num_global_policies):
            for i in range(0, num_region_policies):
                policies = [j] + [i]*len(regions)
                y = run_program(policies, regions)
                opt.tell(policies, y)
        dump(opt.get_result(), 'lulesh.pkl')
    # Run BO iters.
    for i in range(150):
        suggested = opt.ask()
        y = run_program(suggested, regions)
        opt.tell(suggested, y)
        print('iteration:', i, suggested, y)
    print(opt.get_result())

if __name__ == "__main__":
    main()
