#ifndef APOLLO_INSTR_H
#define APOLLO_INSTR_H

#ifdef ENABLE_APOLLO

#include <stdint.h>
#include <omp.h>
#include <assert.h>
#include <stdio.h>

#define STRINGIZE_DETAIL(x) #x
#define STRINGIZE(x) STRINGIZE_DETAIL(x)
#define LOC (__FILE_NAME__ "@" STRINGIZE(__LINE__))
#define asize(x) (int)(sizeof(x)/sizeof(x[0]))

enum {
    CLOSE = 3,
    SPREAD = 4
};

#if defined(RUBY_MACHINE)
static const int nthreads[] = {4,8,14,28,42,56,70,84,98,112};
static const omp_sched_t sched[] = {omp_sched_static, omp_sched_dynamic, omp_sched_guided};
static const int chunk[] = {0,1,4,8,32,64,128,256,512};

#elif defined(LASSEN_MACHINE)
static const int nthreads[] = {160, 80, 40, 20};
static const omp_sched_t sched[] = {
    (omp_sched_t)(omp_sched_static | omp_sched_monotonic), omp_sched_dynamic,
    omp_sched_guided};
static const int chunk[] = {0, 16, 64, 256, 1024};

#else
#error "Ruby or Lassen Machine Unspecified"
static const int nthreads[] = {72, 60, 48, 36, 18};
static const int bind[] = {CLOSE, SPREAD};
static const omp_sched_t sched[] = {omp_sched_static, omp_sched_dynamic, omp_sched_guided};
static const int chunk[] = {0, 4, 16, 64, 256, 1024};

#endif

#define NUM_POLICIES asize(sched)*asize(chunk)

#ifdef __cplusplus
extern "C" {
#endif

    extern void *__apollo_region_create(int num_features,
            const char *id,
            int num_policies,
            int min_training_data,
            const char *model_info);
    extern void __apollo_region_begin(void *r);
    extern void __apollo_region_end(void *r);
    extern void __apollo_region_set_feature(void *r, float feature);
    extern int __apollo_region_get_policy(void *r);

    static int print = 1;

    static int prev_chunk_idx = -1;
    static int prev_sched_idx = -1;
    static int prev_nthreads_idx = -1;

    inline static
        void set_policy(int policy) {
            int chunk_idx = policy % asize(chunk);
            int sched_idx = (policy / asize(chunk)) % asize(sched);
            int nthreads_idx = policy / (asize(chunk) * asize(sched));

#if 1
            if(print) {
                printf(
                    "Policy %d\n"
                    "Set sched 0x%x %s idx %d\n"
                    "Set chunk %d idx %d\n",
                    policy,
                    sched[sched_idx],
                    (sched[sched_idx] ==
                             (omp_sched_static | omp_sched_monotonic)
                         ? "STATIC"
                         : (sched[sched_idx] == omp_sched_dynamic ? "DYNAMIC"
                                                                  : "GUIDED")),
                    sched_idx, chunk[chunk_idx], chunk_idx);
                print = 0;
            }
#endif

#if 0
            if (nthreads_idx != prev_nthreads_idx) {
              omp_set_num_threads(nthreads[nthreads_idx]);
              prev_nthreads_idx = nthreads_idx;
              // printf("Setting num_threads %d\n", nthreads[nthreads_idx]);
            }
#endif

            // Push num threads must be set for every region, takes effect only
            // for the next region.
#if 0
            __kmpc_push_num_threads(NULL, 0, nthreads[nthreads_idx]);
#endif

            // Proc bind must be set for every region, takes effect only for the
            // next region.
            //__kmpc_push_proc_bind(NULL, 0, bind[bind_idx]);

            if (prev_sched_idx != sched_idx || prev_chunk_idx != chunk_idx) {
                omp_set_schedule(sched[sched_idx], chunk[chunk_idx]);
                prev_sched_idx = sched_idx;
                prev_chunk_idx = chunk_idx;
            }
        };

#ifdef __cplusplus
}
#endif

#define APOLLO_BEGIN(FEATURE) \
{ \
    static void* region_handle = NULL; \
    if (region_handle == NULL) \
    region_handle = __apollo_region_create(1, LOC, NUM_POLICIES, 0, ""); \
    __apollo_region_begin(region_handle); \
    __apollo_region_set_feature(region_handle, FEATURE); \
    set_policy(__apollo_region_get_policy(region_handle));

#define APOLLO_END \
    __apollo_region_end(region_handle); \
}

#else // ! ENABLE_APOLLO

#define APOLLO_BEGIN(FEATURE)
#define APOLLO_END

#endif // ENABLE_APOLLO

#endif // APOLLO_INSTR_H

