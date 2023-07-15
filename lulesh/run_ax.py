#!/usr/bin/env python3

import subprocess
import os
import csv
import re
import sys
from functools import partial
from ax.service.managed_loop import optimize

def run_program(policies):

    print(policies)
    input('k')
    num_threads = [160, 80, 40, 20]

    env = os.environ.copy()

    policies_str = ','.join([f'{r}={p}' for r, p in policies.items()])
    env['APOLLO_POLICY_MODEL'] = f'StaticRegion,{policies_str}'
    env['OMP_NUM_THREADS'] = str(num_threads[policies[0]])

    #policy = policies['static']
    #env['APOLLO_POLICY_MODEL'] = f'Static,policy={policy}'

    env['OMP_PLACES'] = 'threads'
    print('env', env['APOLLO_POLICY_MODEL'])
    cmd = "./lulesh2.0 -s 60 -p 50 -i 10"
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
    with open('.apollo/apollo_exec_info.csv', 'r') as f:
        csv_data = csv.DictReader(f, fieldnames=['region', 'execs'])
        regions = [row['region'] for row in csv_data]
    parameters = []
    parameters.append({ 'name' : 'global', 'type' : 'range', 'bounds': [0, 4],
        'value_type' : 'int' })
    for r in regions:
        parameters.append({ 'name' : r, 'type' : 'range', 'bounds': [0, 29],
            'value_type' : 'int' })

    #parameters = [{ 'name' : 'static', 'type' : 'range', 'bounds': [0, 119] }]

    print('Runnning Ax bo...')
    best_params, values, experiment, model = optimize(
            parameters=parameters,
            evaluation_function=run_program,
            minimize=True,
            total_trials=100,
            )
    print('best_params', best_params)
    print('values', values)
    print('experiment', experiment)
    print('model', model)

if __name__ == "__main__":
    main()
