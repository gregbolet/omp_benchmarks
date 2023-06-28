#!/bin/bash

#check if we are on ruby or lassen, load appropriate modules
name=$(uname -n)

if [[ $name == *"ruby"* ]]; then 
	echo "RUBY Machine Detected";
	module load python/3.10.8
	module load cmake/3.23.1
	module load clang/14.0.6
	export OMP_NUM_THREADS=112
	export APOLLO_INSTALL=/g/g15/bolet1/workspace/apollo/build-ruby/install
elif [[ $name == *"lassen"* ]]; then
	echo "LASSEN Machine Detected";
	module load clang/15.0.6
	module load cmake/3.23.1
	module load python/3.8.2
	export OMP_NUM_THREADS=160
	export APOLLO_INSTALL=/g/g15/bolet1/workspace/apollo/build-lassen/install
fi


# set the ROOT_DIR to this script path
export ROOT_DIR=$(dirname $(realpath $BASH_SOURCE))
echo $ROOT_DIR

# need to set your APOLLO_INSTALL envvar for using Apollo
#export APOLLO_INSTALL=/p/vast1/ggeorgak/projects/apollo/apollo/build-quartz/install

