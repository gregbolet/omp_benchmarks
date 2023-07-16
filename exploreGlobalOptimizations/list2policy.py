#!/usr/bin/env python

import numpy as np
import csv

with open('.apollo/apollo_exec_info.csv', 'r') as f:
    csv_data = csv.DictReader(f, fieldnames=['region', 'execs'])
    regions = [row['region'] for row in csv_data]

num_threads = [160, 80, 40, 20]
places = ['threads', 'cores', 'sockets']
bind = [ 'close', 'spread' ]

x = np.fromstring('3.999       1.8403593   0.         14.999       0.         14.84818784 \
 14.999      14.999      14.999       0.         14.999       0. \
  14.988015    0.          0.          0.         14.9304468  14.999 \
    0.          0.         13.18697602 14.999      14.8368685  14.999 \
     14.999       0.          0.          0.27289566  0.         14.21082131 \
       0.         14.999       0.       ', dtype=float, sep=' ')

region_policies = zip(regions, x[3:])
rp_str = ','.join([f'{r}={int(np.floor(k))}' for r, k in region_policies])
print(
        f'OMP_NUM_THREADS={num_threads[int(np.floor(x[0]))]}',
        f'OMP_PLACES={places[int(np.floor(x[1]))]}', 
        f'OMP_PROC_BIND={bind[int(np.floor(x[2]))]}',
        f'APOLLO_POLICY_MODEL=StaticRegion,{rp_str}')

