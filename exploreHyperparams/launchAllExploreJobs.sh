#!/bin/bash

echo "launching exploration jobs"

progs=(bt_nas cg_nas ft_nas bfs_rodinia hpcg lulesh cfd_rodinia)
probsizes=(smlprob medprob)

for prob in "${probsizes[@]}"; do
	for prog in "${progs[@]}"; do

		# default is for small problem size (40 runs per node, 60 minutes each node)
		jobsPerNode=40
		timePerNode=60

		if [ "$prob" = "medprob" ]; then
			jobsPerNode=12
			timePerNode=120
		elif [ "$prob" = "lrgprob" ]; then
			jobsPerNode=4
			timePerNode=240
		fi

		echo "launching ${prog} ${prob} with: ${jobsPerNode} ${timePerNode}"
		python3 setupAndLaunchSbatchJobs.py --progName=${prog} --probSize=${prob} --numTrials=3 --jobsPerNode=${jobsPerNode} --nodeRuntime=${timePerNode}
	done
done


