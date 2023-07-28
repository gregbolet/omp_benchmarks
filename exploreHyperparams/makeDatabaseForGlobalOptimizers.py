#!/usr/bin/env python3

import pandas as pd
import numpy as np
from benchmarks import *
import glob
import os, sys


# for each of the programs/prob sizes in the explorData directory,
# load up all their CSV data

print(ROOT_DIR)
os.chdir(ROOT_DIR+'/explorData')

# extract the names and problem sizes of the done codes
dirs = list(os.listdir())

dirs.sort()

globalDataset = pd.DataFrame()

for dir in dirs:
	progname = dir.split('-')[0]
	probsize = dir.split('-')[1]

	allJobs = glob.glob('./'+dir+'/allUniquePointsToSample.csv')[0]
	doneFiles = glob.glob('./'+dir+'/*/complete.csv')

	allData = pd.read_csv(allJobs)

	doneData = pd.DataFrame(columns=['xtime']+list(allData.columns))

	# join all the done files into one csv
	for doneFile in doneFiles:
		comp = pd.read_csv(doneFile)
		doneData = pd.concat([doneData, comp], ignore_index=True)

	doneData = doneData.reset_index(drop=True)

	# we remove this line just to get the plots up
	doneData = doneData[doneData['xtime'] != -1.0]


	# if we have all the data, let's analyze it
	if doneData.shape[0] == allData.shape[0]:
		# some of the runs didn't get the schedule chunk-size of 4.
		# they must be some newer runs we forgot about, so we're dropping them
		# we're not including them in the analysis or the final report
		doneData = doneData[(doneData['OMP_SCHEDULE'] != 'static,4' ) & 
							          (doneData['OMP_SCHEDULE'] != 'dynamic,4') &
							          (doneData['OMP_SCHEDULE'] != 'guided,4' ) ]
		print(progname, probsize, end='\t')
		print(doneData.shape, allData.shape, 'all samples collected!')
		globalDataset = pd.concat([globalDataset, doneData], ignore_index=True)
	else:
		print('\t', progname, probsize, end='\t')
		print('incomplete data! Collected', doneData.shape[0], '/', allData.shape[0], 'samples')



# now that we've read in all the results, let's save them to a file
print(globalDataset.shape, globalDataset.columns)
print(globalDataset.head(), globalDataset.tail())

# group and average out all the xtimes - include a column for stddev
hparams = list(globalDataset.columns)
hparams.remove('xtime')

avrgd = globalDataset.groupby(hparams).mean().reset_index()
avrgd['stddev'] = globalDataset.groupby(hparams).std().reset_index()['xtime']

print(avrgd.tail())

print('OMP_NUM_THREADS unique', len(list(avrgd['OMP_NUM_THREADS'].unique())))
print('OMP_PROC_BIND unique', len(list(avrgd['OMP_PROC_BIND'].unique())))
print('OMP_PLACES unique', len(list(avrgd['OMP_PLACES'].unique())))
print('OMP_SCHEDULE unique', len(list(avrgd['OMP_SCHEDULE'].unique())))


avrgd.to_csv(ROOT_DIR+'/'+MACHINE+'-fullExplorDataset.csv', index=False)
#globalDataset.to_csv(ROOT_DIR+'/'+MACHINE+'-fullExplorDataset.csv', index=False)


