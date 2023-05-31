## Required Environment Variables for building

LLVM_INSTALL="path/to/llvm/build/install_dir"
APOLLO_INSTALL="path/to/apollo/build/install_dir"
APOLLO_CPU_POLICIES="56,48,44,36,32,28,20,12,8,4,1,112"

## Runtime Note
ALL these codes have had their `#pragma omp for` regions modified to have `schedule(runtime)` included.
This means that we can set the `OMP_SCHEDULE` environment variable to control the OMP for loop schedule and chunk size without needing to manually set it and rebuild for each code.

## NAS Parallel Benchmarks Build Note
For codes from the NPB suite, you'll need to type:
`make bt CLASS=C APOLLO_BUILD=1`
if you want it to use Apollo instrumentation, otherwise you can leave out the `APOLLO_BUILD` flag.