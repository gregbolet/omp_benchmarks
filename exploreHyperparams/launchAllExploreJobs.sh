#!/bin/bash

echo "launching exploration jobs"

#progs=(bt_nas cg_nas ft_nas bfs_rodinia hpcg lulesh cfd_rodinia)
#progs=(lulesh cfd_rodinia)
progs=(hpcg lulesh cfd_rodinia)
probsizes=(smlprob medprob lrgprob)

for prob in "${probsizes[@]}"; do
	for prog in "${progs[@]}"; do

		# default is for small problem size (40 runs per node, 60 minutes each node)
		jobsPerNode=500
		timePerNode=480

		if [ "$prob" = "medprob" ]; then
			jobsPerNode=300
			timePerNode=480
		elif [ "$prob" = "lrgprob" ]; then
			jobsPerNode=200
			timePerNode=480
		fi

		printf "\n\n\n"
		echo "launching ${prog} ${prob} with: ${jobsPerNode} ${timePerNode}"
		python3 setupAndLaunchSbatchJobs.py --progName=${prog} --probSize=${prob} --numTrials=3 --jobsPerNode=${jobsPerNode} --nodeRuntime=${timePerNode}
	done
done


