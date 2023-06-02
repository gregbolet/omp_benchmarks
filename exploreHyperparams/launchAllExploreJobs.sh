#!/bin/bash

source ~/workspace/py3.10.8-gregvirtenv/bin/activate

echo "launching sobol jobs"

progs=(nas_ft nas_cg nas_bt lulesh)
probsizes=(medprob)
rngs=(6739 17)
sobolPoints=(256 512 128)

for prob in "${probsizes[@]}"; do
	for n in "${sobolPoints[@]}"; do
		for prog in "${progs[@]}"; do
			for rng in "${rngs[@]}"; do

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
	done
done


