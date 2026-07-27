/*
 * C++ OpenMP domain vectorized lid-driven cavity solver
 *
 * OpenMP-only lid-driven cavity domain solver.
 * This is the shared-memory counterpart to the MPI-domain and hybrid MPI+OpenMP
 * domain-decomposition solvers in this repository.
 *
 * Numerical formulation: 2D incompressible Navier-Stokes in streamfunction-vorticity form.
 * Kernel style: SIMD/vectorization-friendly OpenMP local kernels.
 */

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <cfloat>
#include <sys/stat.h>
#include <ctime>
#include <cctype>
#ifdef _OPENMP
#include <omp.h>
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

typedef struct {
    int N;
    int Re;
    int steps;
    int poisson_iters;
    double lid_velocity;
    double cfl;
    double max_dt;
    double poisson_tol;
    char poisson_solver[32];
    double sor_omega;
    char scheme[32];
    char out_dir[512];
    int write_fields;
} Config;

static inline int ID(int i, int j, int N) { return i * N + j; }
static int str_eq(const char* a, const char* b) { return strcmp(a, b) == 0; }
static void lower_inplace(char* s) { for (; *s; ++s) *s = (char)tolower((unsigned char)*s); }

static double wall_time(void) {
#ifdef _OPENMP
    return omp_get_wtime();
#else
    return (double)clock() / (double)CLOCKS_PER_SEC;
#endif
}

static void ensure_dir(const char* dir) {
    char tmp[512];
    snprintf(tmp, sizeof(tmp), "%s", dir);
    for (char* p = tmp + 1; *p; ++p) {
        if (*p == '/') {
            *p = '\0';
            mkdir(tmp, 0775);
            *p = '/';
        }
    }
    mkdir(tmp, 0775);
}

static void defaults(Config* cfg) {
    cfg->N = 64;
    cfg->Re = 100;
    cfg->steps = 2000;
    cfg->poisson_iters = 250;
    cfg->lid_velocity = 1.0;
    cfg->cfl = 0.25;
    cfg->max_dt = 0.0025;
    cfg->poisson_tol = 1e-6;
    strcpy(cfg->poisson_solver, "rbgs");
    cfg->sor_omega = 1.7;
    strcpy(cfg->scheme, "upwind");
    strcpy(cfg->out_dir, "results/data");
    cfg->write_fields = 1;
}

static const char* need_value(int* i, int argc, char** argv, const char* opt) {
    if (*i + 1 >= argc) { fprintf(stderr, "Missing value after %s\n", opt); exit(2); }
    (*i)++;
    return argv[*i];
}

static void parse_args(Config* cfg, int argc, char** argv) {
    defaults(cfg);
    for (int i=1; i<argc; ++i) {
        const char* a = argv[i];
        if (str_eq(a, "--N")) cfg->N = atoi(need_value(&i, argc, argv, a));
        else if (str_eq(a, "--Re")) cfg->Re = atoi(need_value(&i, argc, argv, a));
        else if (str_eq(a, "--steps")) cfg->steps = atoi(need_value(&i, argc, argv, a));
        else if (str_eq(a, "--poisson-iters")) cfg->poisson_iters = atoi(need_value(&i, argc, argv, a));
        else if (str_eq(a, "--poisson-tol")) cfg->poisson_tol = atof(need_value(&i, argc, argv, a));
        else if (str_eq(a, "--poisson-solver") || str_eq(a, "--pressure")) { strncpy(cfg->poisson_solver, need_value(&i, argc, argv, a), sizeof(cfg->poisson_solver)-1); cfg->poisson_solver[sizeof(cfg->poisson_solver)-1] = '\0'; lower_inplace(cfg->poisson_solver); }
        else if (str_eq(a, "--sor-omega")) cfg->sor_omega = atof(need_value(&i, argc, argv, a));
        else if (str_eq(a, "--scheme")) strncpy(cfg->scheme, need_value(&i, argc, argv, a), sizeof(cfg->scheme)-1);
        else if (str_eq(a, "--out-dir")) strncpy(cfg->out_dir, need_value(&i, argc, argv, a), sizeof(cfg->out_dir)-1);
        else if (str_eq(a, "--no-fields")) cfg->write_fields = 0;
        else if (str_eq(a, "--help") || str_eq(a, "-h")) {
            printf("cpp_openmp_domain_vectorized OpenMP domain solver\n");
            printf("Options: --N <int> --Re <int> --steps <int> --poisson-iters <int> --poisson-solver jacobi|RBGS|RBSOR --sor-omega <float> --scheme upwind|central --no-fields\n");
            exit(0);
        } else {
            fprintf(stderr, "Unknown argument: %s\n", a);
            exit(2);
        }
    }
    if (cfg->N < 8) { fprintf(stderr, "N must be >= 8\n"); exit(2); }
    if (cfg->Re <= 0) { fprintf(stderr, "Re must be positive\n"); exit(2); }
    if (!str_eq(cfg->scheme, "upwind") && !str_eq(cfg->scheme, "central")) { fprintf(stderr, "scheme must be upwind or central\n"); exit(2); }
    if (!str_eq(cfg->poisson_solver, "jacobi") && !str_eq(cfg->poisson_solver, "rbgs") && !str_eq(cfg->poisson_solver, "rbsor") && !str_eq(cfg->poisson_solver, "sor")) { fprintf(stderr, "poisson_solver must be jacobi, RBGS, or RBSOR\n"); exit(2); }
    if (cfg->sor_omega <= 0.0 || cfg->sor_omega >= 2.0) { fprintf(stderr, "sor_omega should be between 0 and 2\n"); exit(2); }
}

static void apply_psi_bc(double* psi, int N) {
#pragma omp parallel for schedule(static)
    for (int i=0; i<N; ++i) {
        psi[ID(i,0,N)] = 0.0;
        psi[ID(i,N-1,N)] = 0.0;
    }
#pragma omp parallel for schedule(static)
    for (int j=0; j<N; ++j) {
        psi[ID(0,j,N)] = 0.0;
        psi[ID(N-1,j,N)] = 0.0;
    }
}

static void apply_omega_bc(double* omega, const double* psi, const Config* cfg) {
    int N = cfg->N;
    double h = 1.0 / (double)(N-1);
    double h2 = h*h;
#pragma omp parallel for schedule(static)
    for (int i=0; i<N; ++i) {
        omega[ID(i,0,N)] = -2.0 * psi[ID(i,1,N)] / h2;
        omega[ID(i,N-1,N)] = -2.0 * psi[ID(i,N-2,N)] / h2;
    }
#pragma omp parallel for schedule(static)
    for (int j=1; j<N-1; ++j) {
        omega[ID(0,j,N)] = -2.0 * psi[ID(1,j,N)] / h2;
        omega[ID(N-1,j,N)] = -2.0 * psi[ID(N-2,j,N)] / h2 - 2.0 * cfg->lid_velocity / h;
    }
}

// Poisson implementation that preserves the original psi pointer.
static double solve_psi_safe(double* psi0, const double* omega, const Config* cfg) {
    int N = cfg->N;
    size_t total = (size_t)N * (size_t)N;
    double h = 1.0 / (double)(N-1);
    double h2 = h*h;
    double change = DBL_MAX;
    int use_rbgs = str_eq(cfg->poisson_solver, "rbgs");
    int use_rbsor = str_eq(cfg->poisson_solver, "rbsor") || str_eq(cfg->poisson_solver, "sor");

    if (!use_rbgs && !use_rbsor) {
        double* a = psi0;
        double* buf = (double*)malloc(total * sizeof(double));
        if (!buf) { fprintf(stderr, "malloc failed\n"); exit(1); }
        double* b = buf;
        memcpy(b, a, total * sizeof(double));
        for (int it=0; it<cfg->poisson_iters; ++it) {
            apply_psi_bc(a, N);
            double local = 0.0;
#pragma omp parallel for schedule(static) reduction(max:local)
            for (int i=1; i<N-1; ++i) {
                for (int j=1; j<N-1; ++j) {
                    double val = 0.25 * (a[ID(i+1,j,N)] + a[ID(i-1,j,N)] + a[ID(i,j+1,N)] + a[ID(i,j-1,N)] + h2 * omega[ID(i,j,N)]);
                    double ch = fabs(val - a[ID(i,j,N)]);
                    if (ch > local) local = ch;
                    b[ID(i,j,N)] = val;
                }
            }
            apply_psi_bc(b, N);
            double* tmp = a; a = b; b = tmp;
            change = local;
            if (change < cfg->poisson_tol) break;
        }
        if (a != psi0) memcpy(psi0, a, total * sizeof(double));
        free(buf);
        return change;
    }

    const double omega_relax = use_rbsor ? cfg->sor_omega : 1.0;
    for (int it=0; it<cfg->poisson_iters; ++it) {
        double local = 0.0;
        apply_psi_bc(psi0, N);
        for (int color=0; color<2; ++color) {
#pragma omp parallel for schedule(static) reduction(max:local)
            for (int i=1; i<N-1; ++i) {
                for (int j=1; j<N-1; ++j) {
                    if (((i + j) & 1) != color) continue;
                    double gs = 0.25 * (psi0[ID(i+1,j,N)] + psi0[ID(i-1,j,N)] + psi0[ID(i,j+1,N)] + psi0[ID(i,j-1,N)] + h2 * omega[ID(i,j,N)]);
                    double old = psi0[ID(i,j,N)];
                    double val = (1.0 - omega_relax) * old + omega_relax * gs;
                    double ch = fabs(val - old);
                    if (ch > local) local = ch;
                    psi0[ID(i,j,N)] = val;
                }
            }
            apply_psi_bc(psi0, N);
        }
        change = local;
        if (change < cfg->poisson_tol) break;
    }
    return change;
}

static double update_omega(double* omega, double* omega_next, const double* psi, const Config* cfg, double dt) {
    int N = cfg->N;
    double h = 1.0 / (double)(N-1);
    double nu = 1.0 / (double)cfg->Re;
    double max_change = 0.0;
#pragma omp parallel for schedule(static) reduction(max:max_change)
    for (int i=1; i<N-1; ++i) {
#pragma omp simd
        for (int j=1; j<N-1; ++j) {
            double u = (psi[ID(i+1,j,N)] - psi[ID(i-1,j,N)]) / (2.0*h);
            double v = -(psi[ID(i,j+1,N)] - psi[ID(i,j-1,N)]) / (2.0*h);
            double dwdx, dwdy;
            if (str_eq(cfg->scheme, "upwind")) {
                dwdx = (u >= 0.0) ? (omega[ID(i,j,N)] - omega[ID(i,j-1,N)]) / h : (omega[ID(i,j+1,N)] - omega[ID(i,j,N)]) / h;
                dwdy = (v >= 0.0) ? (omega[ID(i,j,N)] - omega[ID(i-1,j,N)]) / h : (omega[ID(i+1,j,N)] - omega[ID(i,j,N)]) / h;
            } else {
                dwdx = (omega[ID(i,j+1,N)] - omega[ID(i,j-1,N)]) / (2.0*h);
                dwdy = (omega[ID(i+1,j,N)] - omega[ID(i-1,j,N)]) / (2.0*h);
            }
            double lap = (omega[ID(i+1,j,N)] + omega[ID(i-1,j,N)] + omega[ID(i,j+1,N)] + omega[ID(i,j-1,N)] - 4.0*omega[ID(i,j,N)]) / (h*h);
            double val = omega[ID(i,j,N)] + dt * (-(u*dwdx + v*dwdy) + nu*lap);
            double ch = fabs(val - omega[ID(i,j,N)]);
            if (ch > max_change) max_change = ch;
            omega_next[ID(i,j,N)] = val;
        }
    }
    return max_change;
}

static double compute_max_velocity(const double* psi, int N) {
    double h = 1.0 / (double)(N-1);
    double umax = 0.0;
#pragma omp parallel for schedule(static) reduction(max:umax)
    for (int i=1; i<N-1; ++i) {
#pragma omp simd
        for (int j=1; j<N-1; ++j) {
            double u = (psi[ID(i+1,j,N)] - psi[ID(i-1,j,N)]) / (2.0*h);
            double v = -(psi[ID(i,j+1,N)] - psi[ID(i,j-1,N)]) / (2.0*h);
            double mag = sqrt(u*u + v*v);
            if (mag > umax) umax = mag;
        }
    }
    if (umax < 1e-12) umax = 1.0;
    return umax;
}

static void write_summary(const Config* cfg, double runtime, double omega_change, double psi_change, double max_u) {
    ensure_dir(cfg->out_dir);
    char path[1024];
    snprintf(path, sizeof(path), "%s/cpp_openmp_domain_vectorized_summary.csv", cfg->out_dir);
    FILE* f = fopen(path, "w");
    if (!f) { perror("summary fopen"); return; }
    fprintf(f, "Implementation,N,Re,Scheme,PoissonSolver,SOROmega,Steps,PoissonIters,OMPThreads,Runtime_s,FinalOmegaChange,FinalPsiChange,MaxVelocity\n");
#ifdef _OPENMP
    int threads = omp_get_max_threads();
#else
    int threads = 1;
#endif
    fprintf(f, "cpp_openmp_domain_vectorized,%d,%d,%s,%s,%.3f,%d,%d,%d,%.10f,%.10e,%.10e,%.10e\n", cfg->N, cfg->Re, cfg->scheme, cfg->poisson_solver, cfg->sor_omega, cfg->steps, cfg->poisson_iters, threads, runtime, omega_change, psi_change, max_u);
    fclose(f);
}

static void write_fields(const Config* cfg, const double* psi, const double* omega) {
    if (!cfg->write_fields) return;
    int N = cfg->N;
    ensure_dir(cfg->out_dir);
    char path[1024];
    snprintf(path, sizeof(path), "%s/cpp_openmp_domain_vectorized_N%d_Re%d_%s_fields.csv", cfg->out_dir, N, cfg->Re, cfg->scheme);
    FILE* f = fopen(path, "w");
    if (!f) { perror("fields fopen"); return; }
    fprintf(f, "i,j,x,y,psi,omega\n");
    double h = 1.0 / (double)(N-1);
    for (int i=0; i<N; ++i) {
        for (int j=0; j<N; ++j) {
            fprintf(f, "%d,%d,%.10g,%.10g,%.12e,%.12e\n", i, j, j*h, i*h, psi[ID(i,j,N)], omega[ID(i,j,N)]);
        }
    }
    fclose(f);
}

int main(int argc, char** argv) {
    Config cfg;
    parse_args(&cfg, argc, argv);
    int N = cfg.N;
    size_t total = (size_t)N * (size_t)N;
    double* psi = (double*)calloc(total, sizeof(double));
    double* omega = (double*)calloc(total, sizeof(double));
    double* omega_next = (double*)calloc(total, sizeof(double));
    if (!psi || !omega || !omega_next) { fprintf(stderr, "allocation failed\n"); return 1; }
    double h = 1.0 / (double)(N-1);
    double nu = 1.0 / (double)cfg.Re;
    double diff_dt = 0.25 * h*h / (nu + 1e-30);
    double dt = fmin(cfg.max_dt, fmin(cfg.cfl*h, diff_dt));

    double t0 = wall_time();
    double omega_change = DBL_MAX;
    double psi_change = DBL_MAX;
    for (int step=0; step<cfg.steps; ++step) {
        apply_psi_bc(psi, N);
        apply_omega_bc(omega, psi, &cfg);
        psi_change = solve_psi_safe(psi, omega, &cfg);
        apply_omega_bc(omega, psi, &cfg);
        memcpy(omega_next, omega, total*sizeof(double));
        omega_change = update_omega(omega, omega_next, psi, &cfg, dt);
        double* tmp = omega; omega = omega_next; omega_next = tmp;
    }
    apply_psi_bc(psi, N);
    apply_omega_bc(omega, psi, &cfg);
    double max_u = compute_max_velocity(psi, N);
    double runtime = wall_time() - t0;
    write_summary(&cfg, runtime, omega_change, psi_change, max_u);
    write_fields(&cfg, psi, omega);
    printf("cpp_openmp_domain_vectorized: N=%d Re=%d scheme=%s steps=%d runtime=%.6f s omega_change=%.3e psi_change=%.3e\n", cfg.N, cfg.Re, cfg.scheme, cfg.steps, runtime, omega_change, psi_change);
    free(psi); free(omega); free(omega_next);
    return 0;
}
