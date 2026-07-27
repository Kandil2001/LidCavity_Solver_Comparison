
/*
 * Hybrid C MPI + OpenMP domain-decomposition lid-driven cavity solver.
 * Kernel style: vectorized/SIMD-friendly local loops.
 *
 * True row-wise domain-decomposition lid-driven cavity solver.
 * Kernel style: vectorized/SIMD-friendly local loops.
 * Each MPI rank owns a horizontal block of rows and exchanges ghost rows with
 * neighbouring ranks. This is different from the older c/mpi and cpp/mpi
 * folders, which distribute independent benchmark cases across MPI ranks.
 *
 * Numerical formulation: 2D incompressible Navier-Stokes in
 * streamfunction-vorticity form on a uniform grid.
 *
 *   Laplace(psi) = -omega
 *   d(omega)/dt + u d(omega)/dx + v d(omega)/dy = nu Laplace(omega)
 *   u = d(psi)/dy, v = -d(psi)/dx
 */

#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <sys/stat.h>
#include <errno.h>
#include <ctype.h>
#ifdef _OPENMP
#include <omp.h>
#endif

typedef struct {
    int N;
    int Re;
    int steps;
    int poisson_iters;
    int output_every;
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

typedef struct {
    int rank;
    int size;
    int row_start;
    int local_n;
    int below;
    int above;
} Decomp;

static inline int ID(int li, int j, int N) { return li * N + j; }

static void die_mpi(const char* msg, MPI_Comm comm) {
    int rank = 0;
    MPI_Comm_rank(comm, &rank);
    if (rank == 0) fprintf(stderr, "ERROR: %s\n", msg);
    MPI_Abort(comm, 1);
}

static int str_eq(const char* a, const char* b) { return strcmp(a, b) == 0; }
static void lower_inplace(char* s) { for (; *s; ++s) *s = (char)tolower((unsigned char)*s); }

static void set_defaults(Config* cfg) {
    cfg->N = 64;
    cfg->Re = 100;
    cfg->steps = 2000;
    cfg->poisson_iters = 250;
    cfg->output_every = 100;
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

static const char* need_value(int* i, int argc, char** argv, const char* opt, MPI_Comm comm) {
    if (*i + 1 >= argc) {
        char buf[256];
        snprintf(buf, sizeof(buf), "Missing value after %s", opt);
        die_mpi(buf, comm);
    }
    (*i)++;
    return argv[*i];
}

static void parse_args(Config* cfg, int argc, char** argv, MPI_Comm comm) {
    set_defaults(cfg);
    for (int i = 1; i < argc; ++i) {
        const char* a = argv[i];
        if (str_eq(a, "--N")) cfg->N = atoi(need_value(&i, argc, argv, a, comm));
        else if (str_eq(a, "--Re")) cfg->Re = atoi(need_value(&i, argc, argv, a, comm));
        else if (str_eq(a, "--steps")) cfg->steps = atoi(need_value(&i, argc, argv, a, comm));
        else if (str_eq(a, "--poisson-iters")) cfg->poisson_iters = atoi(need_value(&i, argc, argv, a, comm));
        else if (str_eq(a, "--poisson-tol")) cfg->poisson_tol = atof(need_value(&i, argc, argv, a, comm));
        else if (str_eq(a, "--poisson-solver") || str_eq(a, "--pressure")) { strncpy(cfg->poisson_solver, need_value(&i, argc, argv, a, comm), sizeof(cfg->poisson_solver)-1); cfg->poisson_solver[sizeof(cfg->poisson_solver)-1] = '\0'; lower_inplace(cfg->poisson_solver); }
        else if (str_eq(a, "--sor-omega")) cfg->sor_omega = atof(need_value(&i, argc, argv, a, comm));
        else if (str_eq(a, "--output-every")) cfg->output_every = atoi(need_value(&i, argc, argv, a, comm));
        else if (str_eq(a, "--scheme")) strncpy(cfg->scheme, need_value(&i, argc, argv, a, comm), sizeof(cfg->scheme)-1);
        else if (str_eq(a, "--out-dir")) strncpy(cfg->out_dir, need_value(&i, argc, argv, a, comm), sizeof(cfg->out_dir)-1);
        else if (str_eq(a, "--no-fields")) cfg->write_fields = 0;
        else if (str_eq(a, "--help") || str_eq(a, "-h")) {
            int rank = 0;
            MPI_Comm_rank(comm, &rank);
            if (rank == 0) {
                printf("Hybrid C MPI+OpenMP domain-decomposition lid-driven cavity solver\n");
                printf("Options:\n");
                printf("  --N <int>                grid size, default 64\n");
                printf("  --Re <int>               Reynolds number, default 100\n");
                printf("  --steps <int>            vorticity time steps, default 2000\n");
                printf("  --poisson-iters <int>    Jacobi iterations per time step, default 250\n");
                printf("  --poisson-tol <float>    Poisson max-change tolerance, default 1e-6\n");
                printf("  --poisson-solver jacobi|RBGS|RBSOR  streamfunction Poisson method, default RBGS\n");
                printf("  --sor-omega <float>      SOR relaxation factor, default 1.7\n");
                printf("  --scheme upwind|central  convection scheme, default upwind\n");
                printf("  --out-dir <path>         output folder, default results/data\n");
                printf("  --no-fields              write summary only\n");
            }
            MPI_Abort(comm, 0);
        } else {
            char buf[256];
            snprintf(buf, sizeof(buf), "Unknown argument: %s", a);
            die_mpi(buf, comm);
        }
    }
    if (cfg->N < 8) die_mpi("N must be at least 8", comm);
    if (cfg->Re <= 0) die_mpi("Re must be positive", comm);
    if (!str_eq(cfg->scheme, "upwind") && !str_eq(cfg->scheme, "central")) die_mpi("scheme must be upwind or central", comm);
    if (!str_eq(cfg->poisson_solver, "jacobi") && !str_eq(cfg->poisson_solver, "rbgs") && !str_eq(cfg->poisson_solver, "rbsor") && !str_eq(cfg->poisson_solver, "sor")) die_mpi("poisson_solver must be jacobi, RBGS, or RBSOR", comm);
    if (cfg->sor_omega <= 0.0 || cfg->sor_omega >= 2.0) die_mpi("sor_omega should be between 0 and 2", comm);
}

static Decomp make_decomp(int N, int rank, int size) {
    Decomp d;
    int base = N / size;
    int rem = N % size;
    d.rank = rank;
    d.size = size;
    d.local_n = base + (rank < rem ? 1 : 0);
    d.row_start = rank * base + (rank < rem ? rank : rem);
    d.below = rank > 0 ? rank - 1 : MPI_PROC_NULL;
    d.above = rank < size - 1 ? rank + 1 : MPI_PROC_NULL;
    return d;
}

static void ensure_dir_rank0(const char* dir, int rank) {
    if (rank == 0) {
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
}

static void exchange_ghost_rows(double* f, const Decomp* d, int N, MPI_Comm comm) {
    MPI_Sendrecv(&f[ID(1, 0, N)], N, MPI_DOUBLE, d->below, 10,
                 &f[ID(d->local_n + 1, 0, N)], N, MPI_DOUBLE, d->above, 10,
                 comm, MPI_STATUS_IGNORE);
    MPI_Sendrecv(&f[ID(d->local_n, 0, N)], N, MPI_DOUBLE, d->above, 20,
                 &f[ID(0, 0, N)], N, MPI_DOUBLE, d->below, 20,
                 comm, MPI_STATUS_IGNORE);
}

static void apply_streamfunction_bc(double* psi, const Decomp* d, int N) {
#pragma omp parallel for schedule(static)
    for (int li = 1; li <= d->local_n; ++li) {
        int gi = d->row_start + li - 1;
        psi[ID(li, 0, N)] = 0.0;
        psi[ID(li, N - 1, N)] = 0.0;
        if (gi == 0 || gi == N - 1) {
            for (int j = 0; j < N; ++j) psi[ID(li, j, N)] = 0.0;
        }
    }
}

static void apply_vorticity_bc(double* omega, const double* psi, const Decomp* d, const Config* cfg) {
    int N = cfg->N;
    double h = 1.0 / (double)(N - 1);
    double h2 = h * h;
#pragma omp parallel for schedule(static)
    for (int li = 1; li <= d->local_n; ++li) {
        int gi = d->row_start + li - 1;
        omega[ID(li, 0, N)] = -2.0 * psi[ID(li, 1, N)] / h2;
        omega[ID(li, N - 1, N)] = -2.0 * psi[ID(li, N - 2, N)] / h2;
        if (gi == 0) {
            for (int j = 1; j < N - 1; ++j) omega[ID(li, j, N)] = -2.0 * psi[ID(li + 1, j, N)] / h2;
        }
        if (gi == N - 1) {
            for (int j = 1; j < N - 1; ++j) omega[ID(li, j, N)] = -2.0 * psi[ID(li - 1, j, N)] / h2 - 2.0 * cfg->lid_velocity / h;
        }
    }
}

static double solve_streamfunction_poisson(double* psi, const double* omega, const Decomp* d, const Config* cfg, MPI_Comm comm) {
    int N = cfg->N;
    int total = (d->local_n + 2) * N;
    double h = 1.0 / (double)(N - 1);
    double h2 = h * h;
    double global_change = DBL_MAX;
    int use_rbgs = str_eq(cfg->poisson_solver, "rbgs");
    int use_rbsor = str_eq(cfg->poisson_solver, "rbsor") || str_eq(cfg->poisson_solver, "sor");

    if (!use_rbgs && !use_rbsor) {
        double* psi_orig = psi;
        double* next = (double*)malloc((size_t)total * sizeof(double));
        if (!next) die_mpi("malloc failed in Poisson solver", comm);
        memcpy(next, psi, (size_t)total * sizeof(double));
        for (int it = 0; it < cfg->poisson_iters; ++it) {
            exchange_ghost_rows(psi, d, N, comm);
            apply_streamfunction_bc(psi, d, N);
            double local_change = 0.0;
            for (int li = 1; li <= d->local_n; ++li) {
                int gi = d->row_start + li - 1;
                if (gi == 0 || gi == N - 1) continue;
                for (int j = 1; j < N - 1; ++j) {
                    double val = 0.25 * (psi[ID(li + 1, j, N)] + psi[ID(li - 1, j, N)] +
                                         psi[ID(li, j + 1, N)] + psi[ID(li, j - 1, N)] +
                                         h2 * omega[ID(li, j, N)]);
                    double ch = fabs(val - psi[ID(li, j, N)]);
                    if (ch > local_change) local_change = ch;
                    next[ID(li, j, N)] = val;
                }
            }
            double* tmp = psi; psi = next; next = tmp;
            apply_streamfunction_bc(psi, d, N);
            MPI_Allreduce(&local_change, &global_change, 1, MPI_DOUBLE, MPI_MAX, comm);
            if (global_change < cfg->poisson_tol) break;
        }
        if (psi != psi_orig) { memcpy(psi_orig, psi, (size_t)total * sizeof(double)); free(psi); }
        else { free(next); }
        return global_change;
    }

    const double omega_relax = use_rbsor ? cfg->sor_omega : 1.0;
    for (int it = 0; it < cfg->poisson_iters; ++it) {
        double local_change = 0.0;
        exchange_ghost_rows(psi, d, N, comm);
        apply_streamfunction_bc(psi, d, N);
        for (int color = 0; color < 2; ++color) {
            for (int li = 1; li <= d->local_n; ++li) {
                int gi = d->row_start + li - 1;
                if (gi == 0 || gi == N - 1) continue;
                for (int j = 1; j < N - 1; ++j) {
                    if (((gi + j) & 1) != color) continue;
                    double gs = 0.25 * (psi[ID(li + 1, j, N)] + psi[ID(li - 1, j, N)] +
                                        psi[ID(li, j + 1, N)] + psi[ID(li, j - 1, N)] +
                                        h2 * omega[ID(li, j, N)]);
                    double old = psi[ID(li, j, N)];
                    double val = (1.0 - omega_relax) * old + omega_relax * gs;
                    double ch = fabs(val - old);
                    if (ch > local_change) local_change = ch;
                    psi[ID(li, j, N)] = val;
                }
            }
            apply_streamfunction_bc(psi, d, N);
            exchange_ghost_rows(psi, d, N, comm);
        }
        MPI_Allreduce(&local_change, &global_change, 1, MPI_DOUBLE, MPI_MAX, comm);
        if (global_change < cfg->poisson_tol) break;
    }
    return global_change;
}

static double compute_velocity_and_max(const double* psi, double* u, double* v, const Decomp* d, const Config* cfg) {
    int N = cfg->N;
    double h = 1.0 / (double)(N - 1);
    double local_umax = 0.0;
#pragma omp parallel for schedule(static) reduction(max:local_umax)
    for (int li = 1; li <= d->local_n; ++li) {
        int gi = d->row_start + li - 1;
        for (int j = 0; j < N; ++j) {
            double uu = 0.0, vv = 0.0;
            if (gi == N - 1) {
                uu = cfg->lid_velocity; vv = 0.0;
            } else if (gi == 0 || j == 0 || j == N - 1) {
                uu = 0.0; vv = 0.0;
            } else {
                uu = (psi[ID(li + 1, j, N)] - psi[ID(li - 1, j, N)]) / (2.0 * h);
                vv = -(psi[ID(li, j + 1, N)] - psi[ID(li, j - 1, N)]) / (2.0 * h);
            }
            u[ID(li, j, N)] = uu;
            v[ID(li, j, N)] = vv;
            double sp = sqrt(uu * uu + vv * vv);
            if (sp > local_umax) local_umax = sp;
        }
    }
    return local_umax;
}

static double advance_vorticity(double* omega, double* omega_next, const double* u, const double* v, const Decomp* d, const Config* cfg, double dt, MPI_Comm comm) {
    int N = cfg->N;
    double h = 1.0 / (double)(N - 1);
    double nu = cfg->lid_velocity / (double)cfg->Re;
    double local_change = 0.0;
#pragma omp parallel for schedule(static) reduction(max:local_change)
    for (int li = 1; li <= d->local_n; ++li) {
        int gi = d->row_start + li - 1;
        if (gi == 0 || gi == N - 1) continue;
        for (int j = 1; j < N - 1; ++j) {
            double dw_dx, dw_dy;
            if (str_eq(cfg->scheme, "central")) {
                dw_dx = (omega[ID(li, j + 1, N)] - omega[ID(li, j - 1, N)]) / (2.0 * h);
                dw_dy = (omega[ID(li + 1, j, N)] - omega[ID(li - 1, j, N)]) / (2.0 * h);
            } else {
                double uu = u[ID(li, j, N)], vv = v[ID(li, j, N)];
                dw_dx = uu >= 0.0 ? (omega[ID(li, j, N)] - omega[ID(li, j - 1, N)]) / h : (omega[ID(li, j + 1, N)] - omega[ID(li, j, N)]) / h;
                dw_dy = vv >= 0.0 ? (omega[ID(li, j, N)] - omega[ID(li - 1, j, N)]) / h : (omega[ID(li + 1, j, N)] - omega[ID(li, j, N)]) / h;
            }
            double lap = (omega[ID(li + 1, j, N)] + omega[ID(li - 1, j, N)] + omega[ID(li, j + 1, N)] + omega[ID(li, j - 1, N)] - 4.0 * omega[ID(li, j, N)]) / (h*h);
            double val = omega[ID(li, j, N)] + dt * (-(u[ID(li, j, N)] * dw_dx + v[ID(li, j, N)] * dw_dy) + nu * lap);
            double ch = fabs(val - omega[ID(li, j, N)]);
            if (ch > local_change) local_change = ch;
            omega_next[ID(li, j, N)] = val;
        }
    }
    double global_change = 0.0;
    MPI_Allreduce(&local_change, &global_change, 1, MPI_DOUBLE, MPI_MAX, comm);
    return global_change;
}

static void gather_owned_field(const double* local, double* global, const Decomp* d, int N, MPI_Comm comm) {
    int size = d->size;
    int* counts = NULL;
    int* displs = NULL;
    if (d->rank == 0) {
        counts = (int*)malloc((size_t)size * sizeof(int));
        displs = (int*)malloc((size_t)size * sizeof(int));
        int offset = 0;
        for (int r = 0; r < size; ++r) {
            int base = N / size;
            int rem = N % size;
            int ln = base + (r < rem ? 1 : 0);
            counts[r] = ln * N;
            displs[r] = offset;
            offset += counts[r];
        }
    }
    MPI_Gatherv((void*)&local[ID(1,0,N)], d->local_n * N, MPI_DOUBLE, global, counts, displs, MPI_DOUBLE, 0, comm);
    if (d->rank == 0) { free(counts); free(displs); }
}

#ifdef _OPENMP
static int openmp_threads(void) { return omp_get_max_threads(); }
#else
static int openmp_threads(void) { return 1; }
#endif

static void write_summary(const Config* cfg, const Decomp* d, double runtime, double omega_change, double psi_change, double umax, int steps_done) {
    if (d->rank != 0) return;
    ensure_dir_rank0(cfg->out_dir, 0);
    char path[1024];
    snprintf(path, sizeof(path), "%s/%s_summary.csv", cfg->out_dir, "c_hybrid_mpi_openmp_vectorized");
    FILE* f = fopen(path, "w");
    if (!f) { fprintf(stderr, "Cannot write %s\n", path); return; }
    fprintf(f, "Implementation,N,Re,Scheme,PoissonSolver,SOROmega,Steps,PoissonIters,MPIRanks,OpenMPThreads,Runtime_s,FinalOmegaChange,FinalPsiChange,MaxVelocity\n");
    fprintf(f, "c_hybrid_mpi_openmp_vectorized,%d,%d,%s,%s,%.3f,%d,%d,%d,%d,%.10f,%.10e,%.10e,%.10e\n",
            cfg->N, cfg->Re, cfg->scheme, cfg->poisson_solver, cfg->sor_omega, steps_done, cfg->poisson_iters, d->size, openmp_threads(), runtime, omega_change, psi_change, umax);
    fclose(f);
}

static void write_fields(const Config* cfg, const Decomp* d, const double* psi, const double* omega, const double* u, const double* v, MPI_Comm comm) {
    int N = cfg->N;
    if (!cfg->write_fields) return;
    double *gpsi = NULL, *gomega = NULL, *gu = NULL, *gv = NULL;
    if (d->rank == 0) {
        size_t n2 = (size_t)N * (size_t)N;
        gpsi = (double*)malloc(n2*sizeof(double));
        gomega = (double*)malloc(n2*sizeof(double));
        gu = (double*)malloc(n2*sizeof(double));
        gv = (double*)malloc(n2*sizeof(double));
    }
    gather_owned_field(psi, gpsi, d, N, comm);
    gather_owned_field(omega, gomega, d, N, comm);
    gather_owned_field(u, gu, d, N, comm);
    gather_owned_field(v, gv, d, N, comm);

    if (d->rank == 0) {
        ensure_dir_rank0(cfg->out_dir, 0);
        char path[1024];
        snprintf(path, sizeof(path), "%s/%s_N%d_Re%d_%s_fields.csv", cfg->out_dir, "c_hybrid_mpi_openmp_vectorized", cfg->N, cfg->Re, cfg->scheme);
        FILE* f = fopen(path, "w");
        if (f) {
            fprintf(f, "i,j,x,y,psi,omega,u,v,speed\n");
            double h = 1.0 / (double)(N - 1);
            for (int i = 0; i < N; ++i) {
                for (int j = 0; j < N; ++j) {
                    int k = i*N + j;
                    double sp = sqrt(gu[k]*gu[k] + gv[k]*gv[k]);
                    fprintf(f, "%d,%d,%.10f,%.10f,%.10e,%.10e,%.10e,%.10e,%.10e\n", i, j, j*h, i*h, gpsi[k], gomega[k], gu[k], gv[k], sp);
                }
            }
            fclose(f);
        }
        free(gpsi); free(gomega); free(gu); free(gv);
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    MPI_Comm comm = MPI_COMM_WORLD;
    int rank = 0, size = 1;
    MPI_Comm_rank(comm, &rank);
    MPI_Comm_size(comm, &size);

    Config cfg;
    parse_args(&cfg, argc, argv, comm);
    Decomp d = make_decomp(cfg.N, rank, size);

    if (d.local_n <= 0) die_mpi("Too many MPI ranks for this grid size", comm);
    int N = cfg.N;
    int total = (d.local_n + 2) * N;
    double* psi = (double*)calloc((size_t)total, sizeof(double));
    double* omega = (double*)calloc((size_t)total, sizeof(double));
    double* omega_next = (double*)calloc((size_t)total, sizeof(double));
    double* u = (double*)calloc((size_t)total, sizeof(double));
    double* v = (double*)calloc((size_t)total, sizeof(double));
    if (!psi || !omega || !omega_next || !u || !v) die_mpi("Allocation failed", comm);

    if (rank == 0) ensure_dir_rank0(cfg.out_dir, 0);
    MPI_Barrier(comm);

    double h = 1.0 / (double)(N - 1);
    double nu = cfg.lid_velocity / (double)cfg.Re;
    double dt_diff = 0.25 * h * h / fmax(nu, 1e-14);
    double dt = fmin(cfg.max_dt, dt_diff);
    double t0 = MPI_Wtime();
    double global_omega_change = DBL_MAX, global_psi_change = DBL_MAX, global_umax = 0.0;
    int steps_done = 0;

    for (int step = 1; step <= cfg.steps; ++step) {
        exchange_ghost_rows(omega, &d, N, comm);
        apply_streamfunction_bc(psi, &d, N);
        apply_vorticity_bc(omega, psi, &d, &cfg);
        global_psi_change = solve_streamfunction_poisson(psi, omega, &d, &cfg, comm);
        exchange_ghost_rows(psi, &d, N, comm);
        double local_umax = compute_velocity_and_max(psi, u, v, &d, &cfg);
        MPI_Allreduce(&local_umax, &global_umax, 1, MPI_DOUBLE, MPI_MAX, comm);
        dt = fmin(cfg.max_dt, cfg.cfl * h / fmax(global_umax, 1e-10));
        dt = fmin(dt, dt_diff);
        memcpy(omega_next, omega, (size_t)total * sizeof(double));
        global_omega_change = advance_vorticity(omega, omega_next, u, v, &d, &cfg, dt, comm);
        double* tmp = omega; omega = omega_next; omega_next = tmp;
        steps_done = step;
        if (step % cfg.output_every == 0 && rank == 0) {
            printf("step=%d omega_change=%.4e psi_change=%.4e umax=%.4e\n", step, global_omega_change, global_psi_change, global_umax);
            fflush(stdout);
        }
        if (global_omega_change < 1e-8 && global_psi_change < cfg.poisson_tol) break;
    }
    double runtime = MPI_Wtime() - t0;
    write_summary(&cfg, &d, runtime, global_omega_change, global_psi_change, global_umax, steps_done);
    write_fields(&cfg, &d, psi, omega, u, v, comm);

    free(psi); free(omega); free(omega_next); free(u); free(v);
    MPI_Finalize();
    return 0;
}
