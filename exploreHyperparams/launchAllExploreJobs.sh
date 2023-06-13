#!/bin/bash

echo "launching exploration jobs"

progs=(nas_ft nas_cg nas_bt lulesh)
probsizes=(medprob, smlprob)

for prob in "${probsizes[@]}"; do
	for prog in "${progs[@]}"; do

		jobsPerNode=16
		timePerNode=10:00:00
		if [ "$prog" = "lulesh" ]; then
			jobsPerNode=10
			timePerNode=6:00:00
		elif [ "$prog" = "nas_ft" ]; then
			jobsPerNode=10
			timePerNode=4:00:00
		else
			jobsPerNode=10
			timePerNode=4:00:00
		fi

		echo "launching ${prog} ${prob} ${rng} ${n} with: ${jobsPerNode} ${timePerNode}"
		python launchSobolExplorJobs.py --progName ${prog} --probSize ${prob} --sobolPoints ${n} --rngSeed ${rng} --nodeRuntime ${timePerNode} --jobsPerNode ${jobsPerNode}
	done
done


