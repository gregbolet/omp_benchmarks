## Objective

The purpose of this repo is to house multiple OMP benchmarks in their closest-to-original (slightly modified) forms where the changes we've made are to enable easy building and OMP schedule control.
What we ultimately want to answer is: 
- *Apart from tuning thread count and thread affinity, can controlling the OMP schedule be useful?*
- *Is the OMP schedule a worth-while hyperparameter for tuning OMP codes?*

Being able to answer these questions will motivate us in designing an LLVM plugin for tuning all three using LLNL's Apollo.
An extension is to then be able to perform a Sobol analysis on the space to see how different code regions interact with each other (and which don't) so as to distinguish regions that should be tuned with more care than others.

## Required Environment Variables for building

### Building without Apollo
`LLVM_INSTALL="path/to/llvm/build/install_dir"` 

This directory should contain the `bin`, `lib`, `share`, `include`, `libexec` subdirectories with `bin/clang` and `bin/clang++` existing.

`OMP_NUM_THREADS="${SOME_NUMBER}"` 

The num threads is required for `CFD` to build. It's used for some `block_length` variable, so you'll need to rebuild `CFD` for any change in thread count.

### Building with Apollo
`APOLLO_INSTALL="path/to/apollo/build/install_dir"`

`APOLLO_CPU_POLICIES="56,48,44,36,32,28,20,12,8,4,1,112"` (this gets passed to the compiler with our custom Apollo pass)

## Building
Look at the Makefile in the root directory to see how the codes are built. If you set the `LLVM_INSTALL` and `OMP_NUM_THREADS` environment variables, you can type `make noapollo` in the root directory of this repo and it should build all the codes without a problem.

## Hardware
Below is a table showing the details of each of the machines we're testing with.

| Machine |              CPU              | NUMA <br>Nodes <br>(Sockets) | Cores<br>-per-<br>Socket | SMT <br>Threads<br>-per-<br>Core | Max <br>SMT<br>Threads |                        Cache <br>Sizes                       |     Cores<br>-per-<br>cache     | DRAM<br>-per-<br>socket |
|:-------:|:-----------------------------:|:----------------------------:|:------------------------:|:--------------------------------:|:----------------------:|:------------------------------------------------------------:|:-------------------------------:|:-----------------------:|
|   Ruby  | Intel Xeon <br>Platinum 8276L |               2              |            28            |                 2                |           112          | L1i:   32 KB<br>L1d:   32 KB<br>L2:  1024 KB<br>L3:    39 MB | L1 + L2: 1 core<br>L3: 28 cores |          93 GB          |
|  Lassen |           IBM Power9          |               2              |            20            |                 4                |           160          | L1i:   32 KB<br>L1d:   32 KB<br>L2:   512 KB<br>L3:    10 MB | L1: 1 core<br>L2 + L3: 2 cores  |          128 GB         |


## Hyperparameters to Explore
For each of these codes, we tune the following OMP runtime parameters. We're ultimately trying to find out whether these runtime parameters are worth tuning for these codes.

|   **Tunable Parameter**   |                               **Explored Values**                               |
|:-------------------------:|:-------------------------------------------------------------------------------:|
|      OMP_NUM_THREADS      | {4,8,14,28,42,56,70,84,98,112} (ruby) <br>{10,20,40,60,80,100,120,140,160} (lassen) |
|       OMP_PROC_BIND       |                                  {close,spread}                                 |
|  OMP_SCHEDULE (schedule)  |                             {static,guided,dynamic}                             |
| OMP_SCHEDULE (chunk size) |                             {1,8,32,64,128,256,512}                             |

From the configuration table, we can note that on the ruby machine we will have to test `10*2*(3*7+1)=440` configurations for each code, while on the lassen machine we will have to test `9*2*(3*7+1)=396` configurations for each code. Given that we have three benchmarks for each program, and we want to do at most 3 repeat trials, we'll be executing `3*3*440=3960` and `3*3*396=3564` runs on ruby and lassen, respectively.

## Code Inputs
Below we show three inputs that we feed to each of the codes. We try a small, medium, and large problem size for each program. We do this to see whether there are execution differences across problem size -- usually due to effects like cache pollution or remote DRAM accesses.

| **Benchmark** |         **Small Input**         |         **Medium Input**        |         **Large Input**         |
|:-------------:|:-------------------------------:|:-------------------------------:|:-------------------------------:|
|      bfs      |   `1 ../inputs/graph4096.txt`   |   `1 ../inputs/graph65536.txt`  |   `1 ../inputs/graph1MW_6.txt`  |
|       bt      |             `bt.B.x`            |             `bt.C.x`            |             `bt.D.x`            |
|      cfd      |        `../inputs/fvcorr.domn.097K`       |       `../inputs/missile.domn.0.2M`       |       `../inputs/missile.domn.0.4M`       |
|       cg      |             `cg.B.x`            |             `cg.C.x`            |             `cg.D.x`            |
|       ft      |             `ft.B.x`            |             `ft.C.x`            |             `ft.D.x`            |
|      hpcg     |    `--nx=64 --ny=64 --nz=64`    |   `--nx=128 --ny=128 --nz=128`  |   `--nx=200 --ny=200 --nz=200`  |
|       lu      |             `lu.B.x`            |             `lu.C.x`            |             `lu.D.x`            |
|     lulesh    | `-s 30 -r 100 -b 0 -c 8 -i 200` | `-s 55 -r 100 -b 0 -c 8 -i 200` | `-s 80 -r 100 -b 0 -c 8 -i 200` |


## Global Search Hyperparameters
Here we list the hyperparemters we explore for each of the global optimization methods.
We do this large exploration using our synthetic data to try and find reasonable configurations of these search methods so that we could apply them on live program tuning.

| **Optimization <br>Method** 	|     **Hyperparameter**     	|                                 **Description**                                	|              **Values**             	|
|:---------------------------:	|:--------------------------:	|:------------------------------------------------------------------------------:	|:-----------------------------------:	|
|              BO             	|      Utility Function      	|              Used for selecting the <br>next best point to sample              	|             {UCB,POI,EI}            	|
|           BO (UCB)          	|            Kappa           	|           Exploration/Exploitation Factor<br>(bigger --> exploration)          	|    start=1<br>stop=500<br>step=1    	|
|           BO (UCB)          	|         Kappa Decay        	|               Kappa variable multiplier <br>(i.e: decay schedule)              	| start=0.01<br>stop=1.5<br>step=0.01 	|
|           BO (UCB)          	|    Kappa Decay <br>Delay   	| Number of iterations that must pass <br>before applying the Kappa Decay factor 	|     start=1<br>stop=50<br>step=1    	|
|       BO <br>(POI, EI)      	|             Xi             	|           Exploration/Exploitation Factor<br>(bigger --> exploration)          	|  start=0.0<br>stop=5.0<br>step=0.1  	|
|             PSO             	|       Population Size      	|              Number of points to sample <br>in one step/iteration              	|     start=1<br>stop=50<br>step=1    	|
|             PSO             	|              w             	|                                  Swarm Inertia                                 	| start=0.01<br>stop=1.0<br>step=0.01 	|
|             PSO             	|             c1             	|                     Personal best bias factor (exploration)                    	| start=0.01<br>stop=1.5<br>step=0.01 	|
|             PSO             	|             c2             	|                     Global best bias factor (exploitation)                     	| start=0.01<br>stop=1.5<br>step=0.01 	|
|             CMA             	|       Population Size      	|              Number of points to sample <br>in one step/iteration              	|     start=1<br>stop=50<br>step=1    	|
|             CMA             	| Population Size <br>Factor 	|               Population Size increase/decrease <br>at each step               	|  start=0.1<br>stop=1.5<br>step=0.1  	|
|             CMA             	|            Sigma           	|                           Initial Standard Deviation                           	|    start=1<br>stop=100<br>step=2    	|

## Notes
### Runtime Note
ALL these codes have had their `#pragma omp for` regions modified to have `schedule(runtime)` included.
This means that we can set the `OMP_SCHEDULE` environment variable to control the OMP for loop schedule and chunk size without needing to manually set it and rebuild for each code.
We also assume each code is being executed from their build directory. We've automated the builds to be written into the `buildNoApollo` and `buildWithApollo` directories within each benchmark directory.

### NPB Note
The NPB codes are from the 2019 SNU NPB suite, where the original Fortran codes were ported over to C. We modified their makefiles and had to include the `npb_common` directory to get these codes to build alone in their own directories.

#### BFS Note
The inputs to BFS are some number of threads and a graph file. If you look at the source, the number of threads passed in goes unused, so we pass in `1` instead.

### Code Versions
* Rodinia 3.1 Codes: `BFS`, `CFD`
* SNU NPB 2019 3.3: `BT`, `CG`, `FT`, `LU`
* HPCG 3.1: `HPCG`
* Lulesh https://github.com/LLNL/LULESH/tree/master -- commit hash `3e01c40b3281aadb7f996525cdd4a3354f6d3801`

