## Required Environment Variables for building

### Building without Apollo
`LLVM_INSTALL="path/to/llvm/build/install_dir"`

### Building with Apollo
`APOLLO_INSTALL="path/to/apollo/build/install_dir"`

`APOLLO_CPU_POLICIES="56,48,44,36,32,28,20,12,8,4,1,112"`

## Building
Look at the Makefile in the root directory to see how the codes are built. If you set the `LLVM_INSTALL` environment variable, you can type `make noapollo` in the root directory of this repo and it should build all the codes without a problem.

## Hyperparameters to Explore
For each of these codes, we tune the following OMP runtime parameters. We're ultimately trying to find out whether these runtime parameters are worth tuning for these codes.

|   **Tunable Parameter**   |                              **Explored Values**                              |
|:-------------------------:|:-----------------------------------------------------------------------------:|
|      OMP_NUM_THREADS      | {4,8,14,28,42,56,70,112} (ruby) <br>{10,20,40,60,80,100,120,140,160} (lassen) |
|       OMP_PROC_BIND       |                                 {close,spread}                                |
|  OMP_SCHEDULE (schedule)  |                            {static,guided,dynamic}                            |
| OMP_SCHEDULE (chunk size) |                            {1,8,32,64,128,256,512}                            |

From the configuration table, we can note that on the ruby machine we will have to test `8*2*3*7=336` configurations for each code, while on the lassen machine we will have to test `9*2*3*7=378` configurations for each code. Given that we have three benchmarks for each program, and we want to do at most 3 repeat trials, we'll be executing `3*3*336=3024` and `3*3*378=3402` runs on ruby and lassen, respectively.

## Code Inputs
Below we show three inputs that we feed to each of the codes. We try a small, medium, and large problem size for each program. We do this to see whether there are execution differences across problem size -- usually due to effects like cache pollution or remote DRAM accesses.

| **Benchmark** |         **Small Input**         |         **Medium Input**        |         **Large Input**         |
|:-------------:|:-------------------------------:|:-------------------------------:|:-------------------------------:|
|      bfs      |        `1 graph4096.txt`        |        `1 graph65536.txt`       |        `1 graph1MW_6.txt`       |
|       bt      |             `bt.B.x`            |             `bt.C.x`            |             `bt.D.x`            |
|      cfd      |        `fvcorr.domn.097K`       |       `missile.domn.0.2M`       |       `missile.domn.0.4M`       |
|       cg      |             `cg.B.x`            |             `cg.C.x`            |             `cg.D.x`            |
|       ft      |             `ft.B.x`            |             `ft.C.x`            |             `ft.D.x`            |
|      hpcg     |    `--nx=16 --ny=16 --nz=16`    |   `--nx=104 --ny=104 --nz=104`  |   `--nx=676 --ny=676 --nz=676`  |
|       lu      |             `lu.B.x`            |             `lu.C.x`            |             `lu.D.x`            |
|     lulesh    | `-s 30 -r 100 -b 0 -c 8 -i 200` | `-s 55 -r 100 -b 0 -c 8 -i 200` | `-s 80 -r 100 -b 0 -c 8 -i 200` |

## Notes
### Runtime Note
ALL these codes have had their `#pragma omp for` regions modified to have `schedule(runtime)` included.
This means that we can set the `OMP_SCHEDULE` environment variable to control the OMP for loop schedule and chunk size without needing to manually set it and rebuild for each code.

### NPB Note
The NPB codes are from the 2019 SNU NPB suite, where the original Fortran codes were ported over to C. We modified their makefiles and had to include the `npb_common` directory to get these codes to build alone in their own directories.

#### BFS Note
The inputs to BFS are some number of threads and a graph file. If you look at the source, the number of threads passed in goes unused, so we pass in `1` instead.

### Code Versions
* Rodinia 3.1 Codes: `BFS`, `CFD`
* SNU NPB 2019 3.3: `BT`, `CG`, `FT`, `LU`
* HPCG 3.1: `HPCG`
* Lulesh https://github.com/LLNL/LULESH/tree/master -- commit hash `3e01c40b3281aadb7f996525cdd4a3354f6d3801`

