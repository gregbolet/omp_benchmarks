//-------------------------------------------------------------------------//
//                                                                         //
//  This benchmark is an OpenCL C version of the NPB CG code. This OpenMP  //
//  C version is developed by the Center for Manycore Programming at Seoul //
//  National University and derived from the OpenMP Fortran versions in    //
//  "NPB3.3-OMP" developed by NAS.                                         //
//                                                                         //
//  Permission to use, copy, distribute and modify this software for any   //
//  purpose with or without fee is hereby granted. This software is        //
//  provided "as is" without express or implied warranty.                  //
//                                                                         //
//  Information on NPB 3.3, including the technical report, the original   //
//  specifications, source code, results and information on how to submit  //
//  new results, is available at:                                          //
//                                                                         //
//           http://www.nas.nasa.gov/Software/NPB/                         //
//                                                                         //
//  Send comments or suggestions for this OpenMP C version to              //
//  cmp@aces.snu.ac.kr                                                     //
//                                                                         //
//          Center for Manycore Programming                                //
//          School of Computer Science and Engineering                     //
//          Seoul National University                                      //
//          Seoul 151-744, Korea                                           //
//                                                                         //
//          E-mail:  cmp@aces.snu.ac.kr                                    //
//                                                                         //
//-------------------------------------------------------------------------//

//-------------------------------------------------------------------------//
// Authors: Sangmin Seo, Jungwon Kim, Jun Lee, Jeongho Nah, Gangwon Jo,    //
//          and Jaejin Lee                                                 //
//-------------------------------------------------------------------------//

//---------------------------------------------------------------------
// program cg
//---------------------------------------------------------------------

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include "globals.h"
#include "randdp.h"
#include "timers.h"
#include "print_results.h"

#include <CL/cl.h>
#include "cl_util.h"

//---------------------------------------------------------------------
/* common / main_int_mem / */
static int colidx[NZ];
static int rowstr[NA + 1];
static int iv[NZ + 1 + NA];
static int arow[NA + 1];
static int acol[NAZ];

/* common / main_flt_mem / */
static double v[NZ];
static double aelt[NAZ];
static double a[NZ];
static double x[NA + 2];
static double z[NA + 2];
static double p[NA + 2];
static double q[NA + 2];
static double r[NA + 2];

/* common /tinof/ */
static int myid;
static int num_threads;
static int ilow;
static int ihigh;

#define MAX_NUM_THREADS 1024
static int last_n[max_threads + 1];

/* common / partit_size / */
static int naa;
static int nzz;
static int firstrow;
static int lastrow;
static int firstcol;
static int lastcol;

/* common /urando/ */
static double amult;
static double tran;

/* common /timers/ */
static logical timeron;
//---------------------------------------------------------------------


//---------------------------------------------------------------------
static cl_device_type device_type;
static cl_device_id device;
static char *device_name;
static cl_context context;
static cl_command_queue cmd_queue;
static cl_program program;

static size_t work_item_sizes[3];
static size_t max_work_group_size;
static size_t max_compute_units;

#define NUM_K_MAIN 2
#define NUM_K_CONJ_GRAD 8
static cl_kernel k_main[NUM_K_MAIN];
static cl_kernel k_cg[NUM_K_CONJ_GRAD];

/* common / main_int_mem / */
static cl_mem m_colidx;
static cl_mem m_rowstr;

/* common / main_flt_mem / */
static cl_mem m_a;
static cl_mem m_x;
static cl_mem m_z;
static cl_mem m_p;
static cl_mem m_q;
static cl_mem m_r;

static cl_mem m_norm_temp1;
static cl_mem m_norm_temp2;
static cl_mem m_rho;
static cl_mem m_d;

static double *g_norm_temp1;
static double *g_norm_temp2;
static double *g_rho;
static double *g_d;

static size_t norm_temp_size;
static size_t rho_size;
static size_t d_size;

static size_t MAIN_0_LWS;
static size_t MAIN_0_GWS;
static size_t CG_LWS;
static size_t CG_GWS;
static size_t CG_LSIZE;
//---------------------------------------------------------------------


//---------------------------------------------------------------------
static void conj_grad(int colidx[],
                      int rowstr[],
                      double x[],
                      double z[],
                      double a[],
                      double p[],
                      double q[],
                      double r[],
                      double *rnorm);
static void makea(int n,
                  int nz,
                  double a[],
                  int colidx[],
                  int rowstr[],
                  int firstrow,
                  int lastrow,
                  int firstcol,
                  int lastcol,
                  int arow[],
                  int acol[][NONZER+1],
                  double aelt[][NONZER+1],
                  double v[],
                  int iv[]);
static void sparse(double a[],
                   int colidx[],
                   int rowstr[],
                   int n,
                   int nz,
                   int nozer,
                   int arow[],
                   int acol[][NONZER+1],
                   double aelt[][NONZER+1],
                   int firstrow,
                   int lastrow,
                   int last_n[],
                   double v[],
                   int iv[],
                   int nzloc[],
                   double rcond,
                   double shift);
static void sprnvc(int n, int nz, int nn1, double v[], int iv[]);
static int icnvrt(double x, int ipwr2);
static void vecset(int n, double v[], int iv[], int *nzv, int i, double val);
static void setup_opencl(int argc, char *argv[], char Class);
static void release_opencl();
//---------------------------------------------------------------------


int main(int argc, char *argv[])
{
  int i, j, k, it;

  double zeta;
  double rnorm;
  double norm_temp1, norm_temp2;

  double t, mflops, tmax;
  char Class;
  logical verified;
  double zeta_verify_value, epsilon, err;

  char *t_names[T_last];

  int gws;
  size_t main_lws[NUM_K_MAIN], main_gws[NUM_K_MAIN];

  cl_int ecode;

  if (argc == 1) {
    fprintf(stderr, "Usage: %s <kernel directory>\n", argv[0]);
    exit(-1);
  }

  for (i = 0; i < T_last; i++) {
    timer_clear(i);
  }

  FILE *fp;
  if ((fp = fopen("timer.flag", "r")) != NULL) {
    timeron = true;
    t_names[T_init] = "init";
    t_names[T_bench] = "benchmk";
    t_names[T_conj_grad] = "conjgd";
    fclose(fp);
  }
  else {
    timeron = false;
  }

  timer_start(T_init);

  firstrow = 0;
  lastrow  = NA-1;
  firstcol = 0;
  lastcol  = NA-1;

  if (NA == 1400 && NONZER == 7 && NITER == 15 && SHIFT == 10) {
    Class = 'S';
    zeta_verify_value = 8.5971775078648;
  } else if (NA == 7000 && NONZER == 8 && NITER == 15 && SHIFT == 12) {
    Class = 'W';
    zeta_verify_value = 10.362595087124;
  } else if (NA == 14000 && NONZER == 11 && NITER == 15 && SHIFT == 20) {
    Class = 'A';
    zeta_verify_value = 17.130235054029;
  } else if (NA == 75000 && NONZER == 13 && NITER == 75 && SHIFT == 60) {
    Class = 'B';
    zeta_verify_value = 22.712745482631;
  } else if (NA == 150000 && NONZER == 15 && NITER == 75 && SHIFT == 110) {
    Class = 'C';
    zeta_verify_value = 28.973605592845;
  } else if (NA == 1500000 && NONZER == 21 && NITER == 100 && SHIFT == 500) {
    Class = 'D';
    zeta_verify_value = 52.514532105794;
  } else if (NA == 9000000 && NONZER == 26 && NITER == 100 && SHIFT == 1500) {
    Class = 'E';
    zeta_verify_value = 77.522164599383;
  } else {
    Class = 'U';
  }

  printf("\n\n NAS Parallel Benchmarks (NPB3.3-OCL) - CG Benchmark\n\n");
  printf(" Size: %11d\n", NA);
  printf(" Iterations:                  %5d\n", NITER);
  printf("\n");

  naa = NA;
  nzz = NZ;

  //---------------------------------------------------------------------
  // Inialize random number generator
  //---------------------------------------------------------------------
  tran    = 314159265.0;
  amult   = 1220703125.0;
  zeta    = randlc(&tran, amult);

  //---------------------------------------------------------------------
  //
  //---------------------------------------------------------------------
  makea(naa, nzz, a, colidx, rowstr,
        firstrow, lastrow, firstcol, lastcol,
        arow,
        (int (*)[NONZER + 1])(void *) acol,
        (double (*)[NONZER + 1])(void *) aelt,
        v, iv);

  //---------------------------------------------------------------------
  // Note: as a result of the above call to makea:
  //    values of j used in indexing rowstr go from 0 --> lastrow-firstrow
  //    values of colidx which are col indexes go from firstcol --> lastcol
  //    So:
  //    Shift the col index vals from actual (firstcol --> lastcol )
  //    to local, i.e., (0 --> lastcol-firstcol)
  //---------------------------------------------------------------------
  for (j = 0; j < lastrow - firstrow + 1; j++) {
    for (k = rowstr[j]; k < rowstr[j + 1]; k++) {
      colidx[k] = colidx[k] - firstcol;
    }
  }

  //---------------------------------------------------------------------
  // set starting vector to (1, 1, .... 1)
  //---------------------------------------------------------------------
  for (i = 0; i < NA+1; i++) {
    x[i] = 1.0;
  }
  for (j = 0; j < lastcol - firstcol + 1; j++) {
    q[j] = 0.0;
    z[j] = 0.0;
    r[j] = 0.0;
    p[j] = 0.0;
  }

  zeta = 0.0;

  setup_opencl(argc, argv, Class);

  timer_stop(T_init);

  printf(" Initialization time = %15.3f seconds\n", timer_read(T_init));

  timer_start(T_bench);

  //---------------------------------------------------------------------
  //---->
  // Main Iteration for inverse power method
  //---->
  //---------------------------------------------------------------------
  for (it = 1; it <= NITER; it++) {
    //---------------------------------------------------------------------
    // The call to the conjugate gradient routine:
    //---------------------------------------------------------------------
    conj_grad(colidx, rowstr, x, z, a, p, q, r, &rnorm);

    //---------------------------------------------------------------------
    // zeta = shift + 1/(x.z)
    // So, first: (x.z)
    // Also, find norm of z
    // So, first: (z.z)
    //---------------------------------------------------------------------
    gws = lastcol - firstcol + 1;
    main_lws[0] = MAIN_0_LWS;
    main_gws[0] = MAIN_0_GWS;

    ecode = clEnqueueWriteBuffer(cmd_queue, m_x,
                                 CL_FALSE, 0,
                                 sizeof(double), x,
                                 0, NULL, NULL);
    clu_CheckError(ecode, "clEnqueueWriteBuffer()");

    ecode = clEnqueueWriteBuffer(cmd_queue, m_z,
                                 CL_TRUE, 0,
                                 sizeof(double), z,
                                 0, NULL, NULL);
    clu_CheckError(ecode, "clEnqueueWriteBuffer()");

    ecode  = clSetKernelArg(k_main[0], 0, sizeof(cl_mem), &m_x);
    ecode |= clSetKernelArg(k_main[0], 1, sizeof(cl_mem), &m_z);
    ecode |= clSetKernelArg(k_main[0], 2, sizeof(cl_mem), &m_norm_temp1);
    ecode |= clSetKernelArg(k_main[0], 3, sizeof(cl_mem), &m_norm_temp2);
    ecode |= clSetKernelArg(k_main[0], 4, sizeof(double) * MAIN_0_LWS, NULL);
    ecode |= clSetKernelArg(k_main[0], 5, sizeof(double) * MAIN_0_LWS, NULL);
    ecode |= clSetKernelArg(k_main[0], 6, sizeof(int), &gws);
    clu_CheckError(ecode, "clSetKernelArg()");

    ecode = clEnqueueNDRangeKernel(cmd_queue,
                                   k_main[0],
                                   1, NULL,
                                   &main_gws[0],
                                   &main_lws[0],
                                   0, NULL, NULL);
    clu_CheckError(ecode, "clEnqueueNDRangeKernel()");

    if (device_type == CL_DEVICE_TYPE_CPU) {
      ecode = clFinish(cmd_queue);
      clu_CheckError(ecode, "clFinish()");
    }
    else {
      CHECK_FINISH();

      ecode = clEnqueueReadBuffer(cmd_queue,
                                  m_norm_temp1,
                                  CL_FALSE, 0,
                                  norm_temp_size,
                                  g_norm_temp1,
                                  0, NULL, NULL);
      clu_CheckError(ecode, "clEnqueueReadBuffer()");

      ecode = clEnqueueReadBuffer(cmd_queue,
                                  m_norm_temp2,
                                  CL_TRUE, 0,
                                  norm_temp_size,
                                  g_norm_temp2,
                                  0, NULL, NULL);
      clu_CheckError(ecode, "clEnqueueReadBuffer()");
    }

    norm_temp1 = 0.0;
    norm_temp2 = 0.0;

    for (j = 0; j < lastcol - firstcol + 1; j++) {
      norm_temp1 += g_norm_temp1[j];
      norm_temp2 += g_norm_temp2[j];
      //norm_temp1 += x[j]*z[j];
      //norm_temp2 += z[j]*z[j];
    }

    norm_temp2 = 1.0 / sqrt(norm_temp2);

    zeta = SHIFT + 1.0 / norm_temp1;
    if (it == 1)
      printf("\n   iteration           ||r||                 zeta\n");
    printf("    %5d       %20.14E%20.13f\n", it, rnorm, zeta);

    //---------------------------------------------------------------------
    // Normalize z to obtain x
    //---------------------------------------------------------------------
    gws = lastcol - firstcol + 1;

    if (device_type == CL_DEVICE_TYPE_CPU) {
      main_lws[1] = CG_LWS;
      main_gws[1] = CG_GWS;
    }
    else {
      main_lws[1] = work_item_sizes[0];
      main_gws[1] = clu_RoundWorkSize((size_t) gws, main_lws[1]);
    }

    ecode = clEnqueueWriteBuffer(cmd_queue,
                                 m_norm_temp2,
                                 CL_TRUE, 0,
                                 sizeof(double),
                                 g_norm_temp2,
                                 0, NULL, NULL);
    clu_CheckError(ecode, "clEnqueueWriteBuffer()");

    ecode = clEnqueueWriteBuffer(cmd_queue, m_z,
                                 CL_FALSE, 0,
                                 sizeof(double), z,
                                 0, NULL, NULL);
    clu_CheckError(ecode, "clEnqueueWriteBuffer()");

    ecode  = clSetKernelArg(k_main[1], 0, sizeof(cl_mem), &m_x);
    ecode |= clSetKernelArg(k_main[1], 1, sizeof(cl_mem), &m_z);
    ecode |= clSetKernelArg(k_main[1], 2, sizeof(double), &norm_temp2);
    clu_CheckError(ecode, "clSetKernelArg()");

    ecode = clEnqueueNDRangeKernel(cmd_queue,
                                   k_main[1],
                                   1, NULL,
                                   &main_gws[1],
                                   &main_lws[1],
                                   0, NULL, NULL);
    clu_CheckError(ecode, "clEnqueueNDRangeKernel()");

    if (device_type == CL_DEVICE_TYPE_CPU) {
      ecode = clFinish(cmd_queue);
      clu_CheckError(ecode, "clFinish()");
    }
    else {
      CHECK_FINISH();

      ecode = clEnqueueReadBuffer(cmd_queue, m_x, CL_TRUE, 0,
                                  (NA + 2) * sizeof(double),
                                  x, 0, NULL, NULL);
      clu_CheckError(ecode, "clEnqueueReadBuffer()");
    }
  } // end of main iter inv pow meth

  ecode = clFinish(cmd_queue);
  clu_CheckError(ecode, "clFinish()");

  timer_stop(T_bench);

  //---------------------------------------------------------------------
  // End of timed section
  //---------------------------------------------------------------------

  t = timer_read(T_bench);

  printf(" Benchmark completed\n");

  epsilon = 1.0e-10;
  if (Class != 'U') {
    err = fabs(zeta - zeta_verify_value) / zeta_verify_value;
    if (err <= epsilon) {
      verified = true;
      printf(" VERIFICATION SUCCESSFUL\n");
      printf(" Zeta is    %20.13E\n", zeta);
      printf(" Error is   %20.13E\n", err);
    } else {
      verified = false;
      printf(" VERIFICATION FAILED\n");
      printf(" Zeta                %20.13E\n", zeta);
      printf(" The correct zeta is %20.13E\n", zeta_verify_value);
    }
  } else {
    verified = false;
    printf(" Problem size unknown\n");
    printf(" NO VERIFICATION PERFORMED\n");
  }

  if (t != 0.0) {
    mflops = (double)(2*NITER*NA)
                   * (3.0+(double)(NONZER*(NONZER+1))
                     + 25.0*(5.0+(double)(NONZER*(NONZER+1)))
                     + 3.0) / t / 1000000.0;
  } else {
    mflops = 0.0;
  }

  print_results("CG", Class, NA, 0, 0,
                NITER, t,
                mflops, "          floating point",
                verified, NPBVERSION, COMPILETIME,
                CS1, CS2, CS3, CS4, CS5, CS6, CS7);

  //---------------------------------------------------------------------
  // More timers
  //---------------------------------------------------------------------
  if (timeron) {
    tmax = timer_read(T_bench);
    if (tmax == 0.0) tmax = 1.0;
    printf("  SECTION   Time (secs)\n");
    for (i = 0; i < T_last; i++) {
      t = timer_read(i);
      if (i == T_init) {
        printf("  %8s:%9.3f\n", t_names[i], t);
      } else {
        printf("  %8s:%9.3f  (%6.2f%%)\n", t_names[i], t, t*100.0/tmax);
        if (i == T_conj_grad) {
          t = tmax - t;
          printf("    --> %8s:%9.3f  (%6.2f%%)\n", "rest", t, t*100.0/tmax);
        }
      }
    }
  }

  return 0;
}


//---------------------------------------------------------------------
// Floaging point arrays here are named as in NPB1 spec discussion of
// CG algorithm
//---------------------------------------------------------------------
static void conj_grad(int colidx[],
                      int rowstr[],
                      double x[],
                      double z[],
                      double a[],
                      double p[],
                      double q[],
                      double r[],
                      double *rnorm)
{
  //---------------------------------------------------------------------
  // input & output buffers in cg
  // 0. x -> p, q, r, z
  // 1. r -> rho
  // 2. rowstr, colidx, a, p -> q
  // 3. p, q -> d
  // 4. p, q, r -> r, z, rho
  // 5. p, r -> p
  // 6. rowstr, colidx, a, z -> r
  // 7. r, x -> d
  //
  // total: rowstr, colidx, a, p, q, r, x -> d, p, q, r, z, rho
  //---------------------------------------------------------------------
  int j, k;
  int cgit, cgitmax = 25;
  double d, sum, rho, rho0, alpha, beta;

  rho = 0.0;

  //---------------------------------------------------------------------
  // Initialize the CG algorithm:
  //---------------------------------------------------------------------
  for (j = 0; j < naa + 1; j++) {
    q[j] = 0.0;
    z[j] = 0.0;
    r[j] = x[j];
    p[j] = r[j];
  }

  //---------------------------------------------------------------------
  // rho = r.r
  // Now, obtain the norm of r: First, sum squares of r elements locally...
  //---------------------------------------------------------------------
  for (j = 0; j < lastcol - firstcol + 1; j++) {
    rho = rho + r[j] * r[j];
  }

  //---------------------------------------------------------------------
  //---->
  // The conj grad iteration loop
  //---->
  //---------------------------------------------------------------------
  for (cgit = 1; cgit <= cgitmax; cgit++) {
    //---------------------------------------------------------------------
    // q = A.p
    // The partition submatrix-vector multiply: use workspace w
    //---------------------------------------------------------------------
    //
    // NOTE: this version of the multiply is actually (slightly: maybe %5)
    //       faster on the sp2 on 16 nodes than is the unrolled-by-2 version
    //       below.   On the Cray t3d, the reverse is true, i.e., the
    //       unrolled-by-two version is some 10% faster.
    //       The unrolled-by-8 version below is significantly faster
    //       on the Cray t3d - overall speed of code is 1.5 times faster.

    for (j = 0; j < lastrow - firstrow + 1; j++) {
      sum = 0.0;
      for (k = rowstr[j]; k < rowstr[j + 1]; k++) {
        sum = sum + a[k] * p[colidx[k]];
      }
      q[j] = sum;
    }

    //---------------------------------------------------------------------
    // Obtain p.q
    //---------------------------------------------------------------------
    d = 0.0;
    for (j = 0; j < lastcol - firstcol + 1; j++) {
      d = d + p[j] * q[j];
    }

    //---------------------------------------------------------------------
    // Obtain alpha = rho / (p.q)
    //---------------------------------------------------------------------
    alpha = rho / d;

    //---------------------------------------------------------------------
    // Save a temporary of rho
    //---------------------------------------------------------------------
    rho0 = rho;

    //---------------------------------------------------------------------
    // Obtain z = z + alpha*p
    // and    r = r - alpha*q
    //---------------------------------------------------------------------
    for (j = 0; j < lastcol - firstcol + 1; j++) {
      z[j] = z[j] + alpha * p[j];
      r[j] = r[j] - alpha * q[j];
    }

    //---------------------------------------------------------------------
    // rho = r.r
    // Now, obtain the norm of r: First, sum squares of r elements locally..
    //---------------------------------------------------------------------
    rho = 0.0;
    for (j = 0; j < lastcol - firstcol + 1; j++) {
      rho = rho + r[j] * r[j];
    }

    //---------------------------------------------------------------------
    // Obtain beta:
    //---------------------------------------------------------------------
    beta = rho / rho0;

    //---------------------------------------------------------------------
    // p = r + beta*p
    //---------------------------------------------------------------------
    for (j = 0; j < lastcol - firstcol + 1; j++) {
      p[j] = r[j] + beta * p[j];
    }
  } // end of do cgit=1,cgitmax

  //---------------------------------------------------------------------
  // Compute residual norm explicitly:  ||r|| = ||x - A.z||
  // First, form A.z
  // The partition submatrix-vector multiply
  //---------------------------------------------------------------------
  sum = 0.0;
  for (j = 0; j < lastrow - firstrow + 1; j++) {
    d = 0.0;
    for (k = rowstr[j]; k < rowstr[j + 1]; k++) {
      d = d + a[k] * z[colidx[k]];
    }
    r[j] = d;
  }

  //---------------------------------------------------------------------
  // At this point, r contains A.z
  //---------------------------------------------------------------------
  for (j = 0; j < lastcol - firstcol + 1; j++) {
    d = x[j] - r[j];
    sum  = sum + d * d;
  }

  *rnorm = sqrt(sum);
}


//---------------------------------------------------------------------
// generate the test problem for benchmark 6
// makea generates a sparse matrix with a
// prescribed sparsity distribution
//
// parameter    type        usage
//
// input
//
// n            i           number of cols/rows of matrix
// nz           i           nonzeros as declared array size
// rcond        r*8         condition number
// shift        r*8         main diagonal shift
//
// output
//
// a            r*8         array for nonzeros
// colidx       i           col indices
// rowstr       i           row pointers
//
// workspace
//
// iv, arow, acol i
// aelt           r*8
//---------------------------------------------------------------------
static void makea(int n,
                  int nz,
                  double a[],
                  int colidx[],
                  int rowstr[],
                  int firstrow,
                  int lastrow,
                  int firstcol,
                  int lastcol,
                  int arow[],
                  int acol[][NONZER+1],
                  double aelt[][NONZER+1],
                  double v[],
                  int iv[])
{
  int iouter, ivelt, nzv, nn1;
  int ivc[NONZER+1];
  double vc[NONZER+1];

  //---------------------------------------------------------------------
  // nonzer is approximately  (int(sqrt(nnza /n)));
  //---------------------------------------------------------------------

  //---------------------------------------------------------------------
  // nn1 is the smallest power of two not less than n
  //---------------------------------------------------------------------
  nn1 = 1;
  do {
    nn1 = 2 * nn1;
  } while (nn1 < n);

  //---------------------------------------------------------------------
  // Generate nonzero positions and save for the use in sparse.
  //---------------------------------------------------------------------
  for (iouter = 0; iouter < ihigh; iouter++) {
    nzv = NONZER;
    sprnvc(n, nzv, nn1, vc, ivc);
    vecset(n, vc, ivc, &nzv, iouter + 1, 0.5);
    arow[iouter] = nzv;

    for (ivelt = 0; ivelt < nzv; ivelt++) {
      acol[iouter][ivelt] = ivc[ivelt] - 1;
      aelt[iouter][ivelt] = vc[ivelt];
    }
  }

  //---------------------------------------------------------------------
  // ... make the sparse matrix from list of elements with duplicates
  //     (v and iv are used as  workspace)
  //---------------------------------------------------------------------
  sparse(a, colidx, rowstr, n, nz, NONZER, arow, acol,
         aelt, firstrow, lastrow, last_n,
         v, &iv[0], &iv[nz], RCOND, SHIFT);
}


//---------------------------------------------------------------------
// rows range from firstrow to lastrow
// the rowstr pointers are defined for nrows = lastrow-firstrow+1 values
//---------------------------------------------------------------------
static void sparse(double a[],
                   int colidx[],
                   int rowstr[],
                   int n,
                   int nz,
                   int nozer,
                   int arow[],
                   int acol[][NONZER+1],
                   double aelt[][NONZER+1],
                   int firstrow,
                   int lastrow,
                   int nzloc[],
                   double rcond,
                   double shift)
{
  int nrows;

  //---------------------------------------------------
  // generate a sparse matrix from a list of
  // [col, row, element] tri
  //---------------------------------------------------
  int i, j, j1, j2, nza, k, kk, nzrow, jcol;
  double size, scale, ratio, va;
  logical cont40;

  //---------------------------------------------------------------------
  // how many rows of result
  //---------------------------------------------------------------------
  nrows = lastrow - firstrow + 1;

  //---------------------------------------------------------------------
  // ...count the number of triples in each row
  //---------------------------------------------------------------------
  for (j = 0; j < nrows+1; j++) {
    rowstr[j] = 0;
  }

  for (i = 0; i < n; i++) {
    for (nza = 0; nza < arow[i]; nza++) {
      j = acol[i][nza] + 1;
      rowstr[j] = rowstr[j] + arow[i];
    }
  }

  rowstr[0] = 0;
  for (j = 1; j < nrows+1; j++) {
    rowstr[j] = rowstr[j] + rowstr[j-1];
  }
  nza = rowstr[nrows] - 1;

  //---------------------------------------------------------------------
  // ... rowstr(j) now is the location of the first nonzero
  //     of row j of a
  //---------------------------------------------------------------------
  if (nza > nz) {
    printf("Space for matrix elements exceeded in sparse\n");
    printf("nza, nzmax = %d, %d\n", nza, nz);
    exit(EXIT_FAILURE);
  }

  //---------------------------------------------------------------------
  // ... preload data pages
  //---------------------------------------------------------------------
  for (j = 0; j < nrows; j++) {
    for (k = rowstr[j]; k < rowstr[j+1]; k++) {
      a[k] = 0.0;
      colidx[k] = -1;
    }
    nzloc[j] = 0;
  }

  //---------------------------------------------------------------------
  // ... generate actual values by summing duplicates
  //---------------------------------------------------------------------
  size = 1.0;
  ratio = pow(rcond, (1.0 / (double)(n)));

  for (i = 0; i < n; i++) {
    for (nza = 0; nza < arow[i]; nza++) {
      j = acol[i][nza];

      scale = size * aelt[i][nza];
      for (nzrow = 0; nzrow < arow[i]; nzrow++) {
        jcol = acol[i][nzrow];
        va = aelt[i][nzrow] * scale;

        //--------------------------------------------------------------------
        // ... add the identity * rcond to the generated matrix to bound
        //     the smallest eigenvalue from below by rcond
        //--------------------------------------------------------------------
        if (jcol == j && j == i) {
          va = va + rcond - shift;
        }

        cont40 = false;
        for (k = rowstr[j]; k < rowstr[j+1]; k++) {
          if (colidx[k] > jcol) {
            //----------------------------------------------------------------
            // ... insert colidx here orderly
            //----------------------------------------------------------------
            for (kk = rowstr[j+1]-2; kk >= k; kk--) {
              if (colidx[kk] > -1) {
                a[kk+1]  = a[kk];
                colidx[kk+1] = colidx[kk];
              }
            }
            colidx[k] = jcol;
            a[k]  = 0.0;
            cont40 = true;
            break;
          } else if (colidx[k] == -1) {
            colidx[k] = jcol;
            cont40 = true;
            break;
          } else if (colidx[k] == jcol) {
            //--------------------------------------------------------------
            // ... mark the duplicated entry
            //--------------------------------------------------------------
            nzloc[j] = nzloc[j] + 1;
            cont40 = true;
            break;
          }
        }
        if (cont40 == false) {
          printf("internal error in sparse: i=%d\n", i);
          exit(EXIT_FAILURE);
        }
        a[k] = a[k] + va;
      }
    }
    size = size * ratio;
  }

  //---------------------------------------------------------------------
  // ... remove empty entries and generate final results
  //---------------------------------------------------------------------
  for (j = 1; j < nrows; j++) {
    nzloc[j] = nzloc[j] + nzloc[j-1];
  }

  for (j = 0; j < nrows; j++) {
    if (j > 0) {
      j1 = rowstr[j] - nzloc[j-1];
    } else {
      j1 = 0;
    }
    j2 = rowstr[j+1] - nzloc[j];
    nza = rowstr[j];
    for (k = j1; k < j2; k++) {
      a[k] = a[nza];
      colidx[k] = colidx[nza];
      nza = nza + 1;
    }
  }
  for (j = 1; j < nrows+1; j++) {
    rowstr[j] = rowstr[j] - nzloc[j-1];
  }
  nza = rowstr[nrows] - 1;
}


//---------------------------------------------------------------------
// generate a sparse n-vector (v, iv)
// having nzv nonzeros
//
// mark(i) is set to 1 if position i is nonzero.
// mark is all zero on entry and is reset to all zero before exit
// this corrects a performance bug found by John G. Lewis, caused by
// reinitialization of mark on every one of the n calls to sprnvc
//---------------------------------------------------------------------
static void sprnvc(int n, int nz, int nn1, double v[], int iv[])
{
  int i, ii, nzv = 0;
  double vecelt, vecloc;

  while (nzv < nz) {
    vecelt = randlc(&tran, amult);

    //---------------------------------------------------------------------
    // generate an integer between 1 and n in a portable manner
    //---------------------------------------------------------------------
    vecloc = randlc(&tran, amult);
    i = icnvrt(vecloc, nn1) + 1;
    if (i > n)
      continue;

    //---------------------------------------------------------------------
    // was this integer generated already?
    //---------------------------------------------------------------------
    logical was_gen = false;

    for (ii = 0; ii < nzv; ii++) {
      if (iv[ii] == i) {
        was_gen = true;
        break;
      }
    }

    if (was_gen)
      continue;

    v[nzv] = vecelt;
    iv[nzv] = i;
    nzv++;
  }
}


//---------------------------------------------------------------------
// scale a double precision number x in (0,1) by a power of 2 and chop it
//---------------------------------------------------------------------
static int icnvrt(double x, int ipwr2)
{
  return (int) (ipwr2 * x);
}


//---------------------------------------------------------------------
// set ith element of sparse vector (v, iv) with
// nzv nonzeros to val
//---------------------------------------------------------------------
static void vecset(int n, double v[], int iv[], int *nzv, int i, double val)
{
  int k;
  logical set = false;

  for (k = 0; k < *nzv; k++) {
    if (iv[k] == i) {
      v[k] = val;
      set = true;
    }
  }
  if (!set) {
    v[*nzv] = val;
    iv[*nzv] = i;
    *nzv++;
  }
}


static void setup_opencl(int argc, char *argv[], char Class)
{
  int i;
  cl_int ecode;
  char *source_dir = "CG";
  source_dir = (argc > 1) ? argv[1] : source_dir;

  // 1. Find the default device type and get a device for the device type
  device_type = clu_GetDefaultDeviceType();
  device = clu_GetAvailableDevice(device_type);
  device_name = clu_GetDeviceName(device);

  ecode = clGetDeviceInfo(device,
                          CL_DEVICE_MAX_WORK_ITEM_SIZES,
                          sizeof(work_item_sizes),
                          &work_item_sizes,
                          NULL);
  clu_CheckError(ecode, "clGetDiviceInfo()");

  ecode = clGetDeviceInfo(device,
                          CL_DEVICE_MAX_WORK_GROUP_SIZE,
                          sizeof(size_t),
                          &max_work_group_size,
                          NULL);
  clu_CheckError(ecode, "clGetDiviceInfo()");

  ecode = clGetDeviceInfo(device,
                          CL_DEVICE_MAX_COMPUTE_UNITS,
                          sizeof(cl_uint),
                          &max_compute_units,
                          NULL);
  clu_CheckError(ecode, "clGetDiviceInfo()");

  // FIXME: The below values are experimental.
#define ROUND(x, y) \
  do { x = ((x) < (y)) ? (x) : (y); } while (0)
#define MAX_SIZE 128
  ROUND(max_work_group_size, DEFAULT_SIZE);
  ROUND(work_item_sizes[0], DEFAULT_SIZE);
  ROUND(work_item_sizes[1], DEFAULT_SIZE);
  ROUND(work_item_sizes[2], DEFAULT_SIZE);

  // 2. Create a context for the specified device
  context = clCreateContext(NULL, 1, &device, NULL, NULL, &ecode);
  clu_CheckError(ecode, "clCreateContext()");

  // 3. Create a command queue
  cmd_queue = clCreateCommandQueue(context, device, 0, &ecode);
  clu_CheckError(ecode, "clCreateCommandQueue()");

  // 4. Build the program
  char *source_file;
  char build_option[100];

  if (device_type == CL_DEVICE_TYPE_CPU) {
    MAIN_0_LWS = 1;
    MAIN_0_GWS = max_compute_units;

    CG_LWS = 1;
    CG_GWS = max_compute_units;

    source_file = "cg_cpu.cl.c"; // FIXME
    sprintf(build_option, "-I. -DCLASS=%d", Class);
  }
  else if (device_type == CL_DEVICE_TYPE_GPU) {
    MAIN_0_LWS = work_item_sizes[0];
    MAIN_0_GWS = clu_RoundWorkSize((size_t)NA, MAIN_0_LWS);

    CG_LWS = work_item_sizes[0];
    CG_GWS = clu_RoundWorkSize((size_t)NA, CG_LWS);

    CG_LSIZE = 64;

    source_file = "cg_gpu.cl.c"; // FIXME
    sprintf(build_option, "-I. -DCLASS=\'%c\' -DLSIZE=%lu -cl-mad-enable",
            Class, CG_LSIZE);
  }
  else {
    fprintf(stderr, "%s: not supported.", clu_GetDeviceTypeName(device_type));
    exit(EXIT_FAILURE);
  }

  program = clu_MakeProgram(context, device, source_dir, source_file,
                            build_option);

  // 5. Create kernels
  char kname[15];

  for (i = 0; i < NUM_K_MAIN; i++) {
    sprintf(kname, "main_%d", i);
    k_main[i] = clCreateKernel(program, kname, &ecode);
    clu_CheckError(ecode, "clCreateKernel()");
  }

  /*
  for (i = 0; i < NUM_K_CONJ_GRAD; i++) {
    sprintf(kname, "conj_grad_%d", i);
    k_conj_grad[i] = clCreateKernel(program, kname, &ecode);
    clu_CheckError(ecode, "clCreateKernel()");
  }
  */

  // 6. Create buffers
  m_colidx = clCreateBuffer(context,
                            CL_MEM_READ_WRITE,
                            NZ * sizeof(int),
                            NULL, &ecode);
  clu_CheckError(ecode, "clCreateBuffer() for m_colidx");

  m_rowstr = clCreateBuffer(context,
                            CL_MEM_READ_WRITE,
                            (NA + 1) * sizeof(int),
                            NULL, &ecode);
  clu_CheckError(ecode, "clCreateBuffer() for m_rowstr");

  m_a = clCreateBuffer(context,
                       CL_MEM_READ_WRITE,
                       NZ * sizeof(double),
                       NULL, &ecode);
  clu_CheckError(ecode, "clCreateBuffer() for m_a");

  m_x = clCreateBuffer(context,
                       CL_MEM_READ_WRITE,
                       (NA + 2) * sizeof(double),
                       NULL, &ecode);
  clu_CheckError(ecode, "clCreateBuffer() for m_x");

  m_z = clCreateBuffer(context,
                       CL_MEM_READ_WRITE,
                       (NA + 2) * sizeof(double),
                       NULL, &ecode);
  clu_CheckError(ecode, "clCreateBuffer() for m_z");

  m_p = clCreateBuffer(context,
                       CL_MEM_READ_WRITE,
                       (NA + 2) * sizeof(double),
                       NULL, &ecode);
  clu_CheckError(ecode, "clCreateBuffer() for m_p");

  m_q = clCreateBuffer(context,
                       CL_MEM_READ_WRITE,
                       (NA + 2) * sizeof(double),
                       NULL, &ecode);
  clu_CheckError(ecode, "clCreateBuffer() for m_q");

  m_r = clCreateBuffer(context,
                       CL_MEM_READ_WRITE,
                       (NA + 2) * sizeof(double),
                       NULL, &ecode);
  clu_CheckError(ecode, "clCreateBuffer() for m_r");

  // reduction buffers
  norm_temp_size = (MAIN_0_GWS/MAIN_0_LWS) * sizeof(double);
  rho_size = (CG_GWS / CG_LWS) * sizeof(double);
  d_size = (CG_GWS / CG_LWS) * sizeof(double);

  g_norm_temp1 = (double *) malloc(norm_temp_size);
  g_norm_temp2 = (double *) malloc(norm_temp_size);
  g_rho = (double *) malloc(rho_size);
  g_d = (double *) malloc(d_size);

  if (device_type == CL_DEVICE_TYPE_CPU) {
    m_norm_temp1 = clCreateBuffer(context,
                                  CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR,
                                  norm_temp_size,
                                  g_norm_temp1, &ecode);
    clu_CheckError(ecode, "clCreateBuffer() for m_norm_temp1");

    m_norm_temp2 = clCreateBuffer(context,
                                  CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR,
                                  norm_temp_size,
                                  g_norm_temp2, &ecode);
    clu_CheckError(ecode, "clCreateBuffer() for m_norm_temp2");

    m_rho = clCreateBuffer(context,
                           CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR,
                           rho_size,
                           g_rho, &ecode);
    clu_CheckError(ecode, "clCreateBuffer() for m_rho");

    m_d = clCreateBuffer(context,
                         CL_MEM_READ_WRITE | CL_MEM_USE_HOST_PTR,
                         d_size,
                         g_d, &ecode);
    clu_CheckError(ecode, "clCreateBuffer() for m_d");
  }
  else {
    m_norm_temp1 = clCreateBuffer(context,
                         CL_MEM_READ_WRITE,
                         norm_temp_size,
                         NULL, &ecode);
    clu_CheckError(ecode, "clCreateBuffer() for m_norm_temp1");

    m_norm_temp2 = clCreateBuffer(context,
                         CL_MEM_READ_WRITE,
                         norm_temp_size,
                         NULL, &ecode);
    clu_CheckError(ecode, "clCreateBuffer() for m_norm_temp2");

    m_rho = clCreateBuffer(context,
                         CL_MEM_READ_WRITE,
                         rho_size,
                         0, &ecode);
    clu_CheckError(ecode, "clCreateBuffer() for m_rho");

    m_d = clCreateBuffer(context,
                         CL_MEM_READ_WRITE,
                         d_size,
                         0, &ecode);
    clu_CheckError(ecode, "clCreateBuffer() for m_d");
  }
}

static void release_opencl()
{
  int i;

  clReleaseMemObject(m_colidx);
  clReleaseMemObject(m_rowstr);
  clReleaseMemObject(m_q);
  clReleaseMemObject(m_z);
  clReleaseMemObject(m_r);
  clReleaseMemObject(m_p);
  clReleaseMemObject(m_x);
  clReleaseMemObject(m_a);

  clReleaseMemObject(m_norm_temp1);
  clReleaseMemObject(m_norm_temp2);
  clReleaseMemObject(m_rho);
  clReleaseMemObject(m_d);

  free(g_norm_temp1);
  free(g_norm_temp2);
  free(g_rho);
  free(g_d);

  for (i = 0; i < NUM_K_MAIN; i++) {
    clReleaseKernel(k_main[i]);
  }
  for (i = 0; i < NUM_K_CONJ_GRAD; i++) {
    clReleaseKernel(k_conj_grad[i]);
  }

  clReleaseProgram(program);
  clReleaseCommandQueue(cmd_queue);
  clReleaseContext(context);
}
