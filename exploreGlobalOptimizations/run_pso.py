#!/usr/bin/env python3

import subprocess
import os
import csv
import re
import sys
import numpy as np
from sko.PSO import PSO

def run_program(policies, wait=False):
    num_threads = [160, 80, 40, 20]
    places = ['threads', 'cores', 'sockets']
    bind = [ 'close', 'spread' ]

    env = os.environ.copy()

    places_policy = int(np.floor(policies['places']))
    env['OMP_PLACES'] = places[places_policy]

    bind_policy = int(np.floor(policies['bind']))
    env['OMP_PROC_BIND'] = str(bind[bind_policy])

    num_threads_policy = int(np.floor(policies['num_threads']))
    env['OMP_NUM_THREADS'] = str(num_threads[num_threads_policy])

    policies_str = ','.join([f'{r}={int(np.floor(p))}' for r, p in
                     policies.items() if r not in ('num_threads', 'places', 'bind')])
    env['APOLLO_POLICY_MODEL'] = f'StaticRegion,{policies_str}'

    print('env places', env['OMP_PLACES'])
    print('env threads', env['OMP_NUM_THREADS'])
    print('env bind', env['OMP_PROC_BIND'])
    print('env apollo', env['APOLLO_POLICY_MODEL'])
    if wait:
        input('k')

    #cmd = "./lulesh2.0 -s 60 -r 50 -i 10 "
    cmd = "./lulesh2.0 -s 100 -r 100 -b 0 -c 8 -i 10"
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

class F_int_dict:
    def __init__(self, keys, f):
        self.keys = keys
        self.f = f
        self.count = 0
    def __call__(self, x):
        x_dict = { 'num_threads' : int(np.floor(x[0])), 'places' : int(np.floor(x[1])), 'bind' : int(np.floor(x[2])) }
        for i, k in enumerate(self.keys):
            #x_dict[k] = int(np.floor(x[3+i]))
            x_dict[k] = int(np.floor(x[3]))
        print('Evaluation', self.count)
        self.count += 1
        return self.f(x_dict, False)

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
    #lower = [0]*(3+len(regions))
    lower = [0]*4
    #upper = [num_threads_policies-1e-3, num_places_policies-1e-3,
    #        num_bind_policies-1e-3] + [num_region_policies-1e-3]*len(regions)
    upper = [num_threads_policies-1e-3, num_places_policies-1e-3,
            num_bind_policies-1e-3, num_region_policies-1e-3]

    #pso = PSO(func=F_int_dict(regions, run_program), n_dim=3+len(regions), pop=10,
    #    lb=lower, ub=upper, w=0.8, c1=0.5, c2=0.5)
    pso = PSO(func=F_int_dict(regions, run_program), n_dim=4, pop=10,
        lb=lower, ub=upper, w=0.8, c1=0.5, c2=0.5)
    pso.run(max_iter=1)
    print('best_x is ', pso.gbest_x, 'best_y is', pso.gbest_y)

if __name__ == "__main__":
    main()
