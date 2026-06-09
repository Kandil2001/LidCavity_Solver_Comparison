/*
 * Serial C lid-driven cavity solver.
 *
 * This file is intentionally self-contained so it can be compiled easily on
 * university clusters, WSL, or a normal Linux terminal. It follows the same
 * CSV contract and case definitions as the MATLAB, C++, and Python solvers.
 *
 * The two implementation labels are benchmark labels only:
 *   - serial_c_looped
 *   - serial_c_vectorized
 * Both paths are serial C. Real OpenMP/MPI/CUDA versions should live in
 * separate folders so the benchmark ladder remains honest and easy to read.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <ctype.h>
#include <float.h>
#include <stdbool.h>
#include <sys/stat.h>
#ifdef _WIN32
#include <direct.h>
#endif

#ifndef M_PI
#define M_PI 3.141592653589793238462643383279502884
#endif

#define MAX_LIST 16
#define IDX(m,i,j) ((i) * (m).n + (j))
#define AT(m,i,j) ((m).a[IDX((m),(i),(j))])

/* -------------------------------------------------------------------------
 * Data structures
 * ------------------------------------------------------------------------- */

typedef struct {
    int n;
    double *a;
} Matrix;

typedef struct {
    double U_lid;
    double L;

    int maxIter;
    int maxIter_N128_bonus;
    int maxIter_Re1000_bonus;
    int maxIter_central_bonus;

    double tol_mass;
    double tol_divergence;
    double tol_velocity;
    double diverged_limit;

    double cfl;
    double dt_max;
    double dt_min;

    double alpha_u;
    double alpha_p;

    int poisson_maxIter;
    double poisson_tol_abs;
    double poisson_tol_rel;
    int poisson_check_every;

    char sor_omega[32];
    double sor_omega_min;
    double sor_omega_max;

    int meshes[MAX_LIST]; int n_meshes;
    int re_list[MAX_LIST]; int n_re;
    char schemes[MAX_LIST][32]; int n_schemes;
    char pressure_solvers[MAX_LIST][32]; int n_pressure;
    char implementations[MAX_LIST][32]; int n_impl;

    double validation_u_L2_limit_Re100;
    double validation_v_L2_limit_Re100;
    double validation_u_L2_limit_Re400;
    double validation_v_L2_limit_Re400;
    double validation_u_L2_limit_Re1000;
    double validation_v_L2_limit_Re1000;

    int save_fields;
    char results_dir[256];
    char data_dir[256];
} Config;

typedef struct {
    int iter;
    int converged;
    double final_true_residual;
    double final_relative_residual;
    double final_change;
    double omega;
} PoissonInfo;

typedef struct {
    int N;
    int Re;
    char scheme[32];
    char pressure_solver[32];
    char implementation[32];

    double *x;
    double *y;
    Matrix u, v, p, speed, vorticity;

    double *Ru, *Rv, *Rc_mass, *Rc_div, *dt, *poisson_relative_residual;
    int *poisson_iters;
    int *poisson_converged;
    int hist_count;
    int hist_cap;

    int iterations;
    int localMaxIter;
    double runtime;
    char status[32];
    double final_Ru;
    double final_Rv;
    double final_Rc_mass;
    double final_Rc_div;
    double avg_poisson_iters;
    double avg_poisson_relative_residual;
    double pressure_saturation_ratio;
    int stagnation_counter;
} Result;

typedef struct {
    int available;
    int pass;
    double u_L2;
    double v_L2;
    double u_Linf;
    double v_Linf;
    double u_limit;
    double v_limit;
} Metrics;

/* -------------------------------------------------------------------------
 * Small utilities
 * ------------------------------------------------------------------------- */

static void die(const char *msg) {
    fprintf(stderr, "ERROR: %s\n", msg);
    exit(1);
}

static double wall_time(void) {
    return (double)clock() / (double)CLOCKS_PER_SEC;
}

static void ensure_dir(const char *path) {
#ifdef _WIN32
    _mkdir(path);
#else
    mkdir(path, 0775);
#endif
}

static void lower_inplace(char *s) {
    for (; *s; ++s) *s = (char)tolower((unsigned char)*s);
}

static void upper_inplace(char *s) {
    for (; *s; ++s) *s = (char)toupper((unsigned char)*s);
}

static void strlower_copy(char *dst, const char *src, size_t n) {
    snprintf(dst, n, "%s", src);
    lower_inplace(dst);
}

static void strupper_copy(char *dst, const char *src, size_t n) {
    snprintf(dst, n, "%s", src);
    upper_inplace(dst);
}

static void normalize_c_implementation(char *dst, const char *src, size_t n) {
    char tmp[64];
    strlower_copy(tmp, src, sizeof(tmp));
    if (strcmp(tmp, "serial_c_vectorized") == 0 || strcmp(tmp, "c_vectorized") == 0 ||
        strcmp(tmp, "vectorized_c") == 0 || strcmp(tmp, "vectorized") == 0) {
        snprintf(dst, n, "serial_c_vectorized");
        return;
    }
    if (strcmp(tmp, "serial_c_looped") == 0 || strcmp(tmp, "c_looped") == 0 ||
        strcmp(tmp, "looped_c") == 0 || strcmp(tmp, "looped") == 0 || strcmp(tmp, "loop") == 0 ||
        strcmp(tmp, "serial_c") == 0 || strcmp(tmp, "c") == 0 || strcmp(tmp, "serial") == 0) {
        snprintf(dst, n, "serial_c_looped");
        return;
    }
    die("Unknown implementation (use serial_c_vectorized or serial_c_looped)");
}

