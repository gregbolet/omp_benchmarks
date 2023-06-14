#!/bin/bash

echo "launching exploration jobs"

progs=(bt_nas cg_nas ft_nas bfs_rodinia hpcg lulesh cfd_rodinia)
probsizes=(smlprob medprob lrgprob)

for prob in "${probsizes[@]}"; do
	for prog in "${progs[@]}"; do

		# default is for small problem size
		jobsPerNode=30
		timePerNode=1:00:00
		if [ "$prog" = "lulesh" ]; then
			jobsPerNode=10
			timePerNode=6:00:00
		elif [ "$prog" = "hpcg" ]; then
			jobsPerNode=10
			timePerNode=4:00:00
		else
			jobsPerNode=10
			timePerNode=4:00:00
		fi

		echo "launching ${prog} ${prob} with: ${jobsPerNode} ${timePerNode}"
		python3 setupAndLaunchSbatchJobs.py --progName=${prog} --probSize=${prob} --numTrials=3 --jobsPerNode=${jobsPerNode} --nodeRuntime=${timePerNode}
	done
done


