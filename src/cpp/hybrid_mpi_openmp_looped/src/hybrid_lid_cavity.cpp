/*
 * Hybrid MPI + OpenMP lid-driven cavity solver.
 *
 * This is a true domain-decomposition example with explicit loop-based local kernels: one CFD domain is split in the
 * vertical direction across MPI ranks. Each rank owns a block of rows and
 * exchanges ghost rows with neighbouring ranks. OpenMP is used inside each rank
 * for shared-memory loop parallelism.
 *
 * Numerical formulation: 2D incompressible Navier-Stokes in
 * streamfunction-vorticity form on a uniform collocated grid.
 *
 *   Laplace(psi) = -omega
 *   d(omega)/dt + u d(omega)/dx + v d(omega)/dy = nu Laplace(omega)
 *   u = d(psi)/dy, v = -d(psi)/dx
 *
 * This implementation is meant as a clear, reproducible domain-decomposition
 * CFD/HPC demonstration. The older cpp/mpi folder is a case-parallel benchmark
 * driver; this folder is the actual MPI domain decomposition solver.
 */

#include <mpi.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace fs = std::filesystem;

struct Config {
    int N = 64;
    int Re = 100;
    int steps = 2000;
    int poisson_iters = 250;
    int output_every = 100;
    double lid_velocity = 1.0;
    double cfl = 0.25;
    double max_dt = 0.0025;
    double poisson_tol = 1e-6;
    std::string poisson_solver = "rbgs";
    double sor_omega = 1.7;
    std::string scheme = "upwind";
    std::string out_dir = "results/data";
    bool write_fields = true;
};

struct Decomp {
    int rank = 0;
    int size = 1;
    int row_start = 0;   // inclusive global row index
    int local_n = 0;     // number of owned rows
    int below = MPI_PROC_NULL;
    int above = MPI_PROC_NULL;
};

static inline int id(int li, int j, int N) {
    return li * N + j;
}

static std::string lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    return s;
}

static Config parse_args(int argc, char** argv) {
    Config cfg;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        auto need_value = [&](const std::string& opt) -> std::string {
            if (i + 1 >= argc) throw std::runtime_error("Missing value after " + opt);
            return argv[++i];
        };
        if (a == "--N") cfg.N = std::stoi(need_value(a));
        else if (a == "--Re") cfg.Re = std::stoi(need_value(a));
        else if (a == "--steps") cfg.steps = std::stoi(need_value(a));
        else if (a == "--poisson-iters") cfg.poisson_iters = std::stoi(need_value(a));
        else if (a == "--poisson-tol") cfg.poisson_tol = std::stod(need_value(a));
        else if (a == "--poisson-solver" || a == "--pressure") cfg.poisson_solver = lower(need_value(a));
        else if (a == "--sor-omega") cfg.sor_omega = std::stod(need_value(a));
        else if (a == "--output-every") cfg.output_every = std::stoi(need_value(a));
        else if (a == "--scheme") cfg.scheme = lower(need_value(a));
        else if (a == "--out-dir") cfg.out_dir = need_value(a);
        else if (a == "--no-fields") cfg.write_fields = false;
        else if (a == "--help" || a == "-h") {
            std::cout << "Hybrid MPI+OpenMP lid-driven cavity solver\n"
                      << "Options:\n"
                      << "  --N <int>                grid size, default 64\n"
                      << "  --Re <int>               Reynolds number, default 100\n"
                      << "  --steps <int>            vorticity time steps, default 2000\n"
                      << "  --poisson-iters <int>    Jacobi iterations per time step, default 250\n"
                      << "  --poisson-tol <float>    early stop tolerance for Poisson max-change, default 1e-6\n"
                      << "  --poisson-solver jacobi|RBGS|RBSOR  streamfunction Poisson method, default RBGS\n"
                      << "  --sor-omega <float>      SOR relaxation factor, default 1.7\n"
                      << "  --scheme upwind|central  convection scheme, default upwind\n"
                      << "  --out-dir <path>         output folder, default results/data\n"
                      << "  --no-fields              write summary only\n";
            MPI_Abort(MPI_COMM_WORLD, 0);
        } else {
            throw std::runtime_error("Unknown argument: " + a);
        }
    }
    if (cfg.N < 8) throw std::runtime_error("N must be at least 8");
    if (cfg.Re <= 0) throw std::runtime_error("Re must be positive");
    if (cfg.scheme != "upwind" && cfg.scheme != "central") throw std::runtime_error("scheme must be upwind or central");
    if (cfg.poisson_solver != "jacobi" && cfg.poisson_solver != "rbgs" && cfg.poisson_solver != "rbsor" && cfg.poisson_solver != "sor") throw std::runtime_error("poisson_solver must be jacobi, RBGS, or RBSOR");
    if (cfg.sor_omega <= 0.0 || cfg.sor_omega >= 2.0) throw std::runtime_error("sor_omega should be between 0 and 2");
    return cfg;
}

static Decomp make_decomp(int N, int rank, int size) {
    Decomp d;
    d.rank = rank;
    d.size = size;
    const int base = N / size;
    const int rem = N % size;
    d.local_n = base + (rank < rem ? 1 : 0);
    d.row_start = rank * base + std::min(rank, rem);
    d.below = (rank > 0) ? rank - 1 : MPI_PROC_NULL;
    d.above = (rank < size - 1) ? rank + 1 : MPI_PROC_NULL;
    return d;
}

static void exchange_ghost_rows(std::vector<double>& f, const Decomp& d, int N, MPI_Comm comm) {
    // local rows are 1..local_n. Row 0 and local_n+1 are ghost rows.
    MPI_Sendrecv(&f[id(1, 0, N)], N, MPI_DOUBLE, d.below, 10,
                 &f[id(d.local_n + 1, 0, N)], N, MPI_DOUBLE, d.above, 10,
                 comm, MPI_STATUS_IGNORE);

    MPI_Sendrecv(&f[id(d.local_n, 0, N)], N, MPI_DOUBLE, d.above, 20,
                 &f[id(0, 0, N)], N, MPI_DOUBLE, d.below, 20,
                 comm, MPI_STATUS_IGNORE);
}

static void apply_streamfunction_bc(std::vector<double>& psi, const Decomp& d, int N) {
    // No penetration: psi is constant on all walls. We use psi=0.
    #pragma omp parallel for schedule(static)
    for (int li = 1; li <= d.local_n; ++li) {
        const int gi = d.row_start + li - 1;
        psi[id(li, 0, N)] = 0.0;
        psi[id(li, N - 1, N)] = 0.0;
        if (gi == 0 || gi == N - 1) {
            for (int j = 0; j < N; ++j) psi[id(li, j, N)] = 0.0;
        }
    }
}

static void apply_vorticity_bc(std::vector<double>& omega, const std::vector<double>& psi, const Decomp& d, const Config& cfg) {
    const int N = cfg.N;
    const double h = 1.0 / static_cast<double>(N - 1);
    const double h2 = h * h;

    #pragma omp parallel for schedule(static)
    for (int li = 1; li <= d.local_n; ++li) {
        const int gi = d.row_start + li - 1;

        // Left and right stationary walls.
        omega[id(li, 0, N)] = -2.0 * psi[id(li, 1, N)] / h2;
        omega[id(li, N - 1, N)] = -2.0 * psi[id(li, N - 2, N)] / h2;

        // Bottom stationary wall.
        if (gi == 0) {
            for (int j = 1; j < N - 1; ++j) {
                omega[id(li, j, N)] = -2.0 * psi[id(li + 1, j, N)] / h2;
            }
        }

        // Top moving lid with u = U_lid.
        if (gi == N - 1) {
            for (int j = 1; j < N - 1; ++j) {
                omega[id(li, j, N)] = -2.0 * psi[id(li - 1, j, N)] / h2 - 2.0 * cfg.lid_velocity / h;
            }
        }
    }
}

static double solve_streamfunction_poisson(
    std::vector<double>& psi,
    const std::vector<double>& omega,
    const Decomp& d,
    const Config& cfg,
    MPI_Comm comm
) {
    const int N = cfg.N;
    const double h = 1.0 / static_cast<double>(N - 1);
    const double h2 = h * h;
    double global_change = std::numeric_limits<double>::infinity();
    const bool use_rbgs = (cfg.poisson_solver == "rbgs");
    const bool use_rbsor = (cfg.poisson_solver == "rbsor" || cfg.poisson_solver == "sor");

    if (!use_rbgs && !use_rbsor) {
        std::vector<double> next = psi;
        for (int it = 0; it < cfg.poisson_iters; ++it) {
            exchange_ghost_rows(psi, d, N, comm);
            apply_streamfunction_bc(psi, d, N);
            double local_change = 0.0;
            for (int li = 1; li <= d.local_n; ++li) {
                const int gi = d.row_start + li - 1;
                if (gi == 0 || gi == N - 1) continue;
                for (int j = 1; j < N - 1; ++j) {
                    const double val = 0.25 * (psi[id(li + 1, j, N)] + psi[id(li - 1, j, N)] + psi[id(li, j + 1, N)] + psi[id(li, j - 1, N)] + h2 * omega[id(li, j, N)]);
                    local_change = std::max(local_change, std::abs(val - psi[id(li, j, N)]));
                    next[id(li, j, N)] = val;
                }
            }
            std::swap(psi, next);
            apply_streamfunction_bc(psi, d, N);
            MPI_Allreduce(&local_change, &global_change, 1, MPI_DOUBLE, MPI_MAX, comm);
            if (global_change < cfg.poisson_tol) break;
        }
        exchange_ghost_rows(psi, d, N, comm);
        return global_change;
    }

    const double omega_relax = use_rbsor ? cfg.sor_omega : 1.0;
    for (int it = 0; it < cfg.poisson_iters; ++it) {
        double local_change = 0.0;
        exchange_ghost_rows(psi, d, N, comm);
        apply_streamfunction_bc(psi, d, N);
        for (int color = 0; color < 2; ++color) {
            for (int li = 1; li <= d.local_n; ++li) {
                const int gi = d.row_start + li - 1;
                if (gi == 0 || gi == N - 1) continue;
                for (int j = 1; j < N - 1; ++j) {
                    if (((gi + j) & 1) != color) continue;
                    const double gs = 0.25 * (psi[id(li + 1, j, N)] + psi[id(li - 1, j, N)] + psi[id(li, j + 1, N)] + psi[id(li, j - 1, N)] + h2 * omega[id(li, j, N)]);
                    const double old = psi[id(li, j, N)];
                    const double val = (1.0 - omega_relax) * old + omega_relax * gs;
                    local_change = std::max(local_change, std::abs(val - old));
                    psi[id(li, j, N)] = val;
                }
            }
            apply_streamfunction_bc(psi, d, N);
            exchange_ghost_rows(psi, d, N, comm);
        }
        MPI_Allreduce(&local_change, &global_change, 1, MPI_DOUBLE, MPI_MAX, comm);
        if (global_change < cfg.poisson_tol) break;
    }
    return global_change;
}

static double compute_velocity_and_max(
    const std::vector<double>& psi,
    std::vector<double>& u,
    std::vector<double>& v,
    const Decomp& d,
    const Config& cfg
) {
    const int N = cfg.N;
    const double h = 1.0 / static_cast<double>(N - 1);
    double local_umax = cfg.lid_velocity;

    #pragma omp parallel for reduction(max:local_umax) schedule(static)
    for (int li = 1; li <= d.local_n; ++li) {
        const int gi = d.row_start + li - 1;
        for (int j = 0; j < N; ++j) {
            double uu = 0.0;
            double vv = 0.0;
            if (gi == N - 1) {
                uu = cfg.lid_velocity;
            } else if (gi > 0 && j > 0 && j < N - 1) {
                uu = (psi[id(li + 1, j, N)] - psi[id(li - 1, j, N)]) / (2.0 * h);
                vv = -(psi[id(li, j + 1, N)] - psi[id(li, j - 1, N)]) / (2.0 * h);
            }
            u[id(li, j, N)] = uu;
            v[id(li, j, N)] = vv;
            local_umax = std::max(local_umax, std::max(std::abs(uu), std::abs(vv)));
        }
    }
    return local_umax;
}

static double advance_vorticity(
    std::vector<double>& omega,
    const std::vector<double>& u,
    const std::vector<double>& v,
    const Decomp& d,
    const Config& cfg,
    double dt
) {
    const int N = cfg.N;
    const double h = 1.0 / static_cast<double>(N - 1);
    const double nu = cfg.lid_velocity / static_cast<double>(cfg.Re);
    std::vector<double> next = omega;
    double local_change = 0.0;

    #pragma omp parallel for reduction(max:local_change) schedule(static)
    for (int li = 1; li <= d.local_n; ++li) {
        const int gi = d.row_start + li - 1;
        if (gi == 0 || gi == N - 1) continue;
        for (int j = 1; j < N - 1; ++j) {
            const double wc = omega[id(li, j, N)];
            double dwdx = 0.0;
            double dwdy = 0.0;
            if (cfg.scheme == "central") {
                dwdx = (omega[id(li, j + 1, N)] - omega[id(li, j - 1, N)]) / (2.0 * h);
                dwdy = (omega[id(li + 1, j, N)] - omega[id(li - 1, j, N)]) / (2.0 * h);
            } else {
                dwdx = (u[id(li, j, N)] >= 0.0)
                    ? (omega[id(li, j, N)] - omega[id(li, j - 1, N)]) / h
                    : (omega[id(li, j + 1, N)] - omega[id(li, j, N)]) / h;
                dwdy = (v[id(li, j, N)] >= 0.0)
                    ? (omega[id(li, j, N)] - omega[id(li - 1, j, N)]) / h
                    : (omega[id(li + 1, j, N)] - omega[id(li, j, N)]) / h;
            }
            const double lap = (omega[id(li + 1, j, N)] + omega[id(li - 1, j, N)] +
                                omega[id(li, j + 1, N)] + omega[id(li, j - 1, N)] - 4.0 * wc) / (h * h);
            const double val = wc + dt * (-(u[id(li, j, N)] * dwdx + v[id(li, j, N)] * dwdy) + nu * lap);
            next[id(li, j, N)] = val;
            local_change = std::max(local_change, std::abs(val - wc));
        }
    }

    omega.swap(next);
    return local_change;
}

static void gather_and_write_fields(
    const std::vector<double>& psi,
    const std::vector<double>& omega,
    const std::vector<double>& u,
    const std::vector<double>& v,
    const Decomp& d,
    const Config& cfg,
    MPI_Comm comm
) {
    const int N = cfg.N;
    std::vector<int> local_counts(d.size, 0), displs(d.size, 0), row_starts(d.size, 0), local_rows(d.size, 0);
    const int send_count = d.local_n * N;

    MPI_Gather(&send_count, 1, MPI_INT, local_counts.data(), 1, MPI_INT, 0, comm);
    MPI_Gather(&d.row_start, 1, MPI_INT, row_starts.data(), 1, MPI_INT, 0, comm);
    MPI_Gather(&d.local_n, 1, MPI_INT, local_rows.data(), 1, MPI_INT, 0, comm);

    int total = 0;
    if (d.rank == 0) {
        for (int r = 0; r < d.size; ++r) {
            displs[r] = total;
            total += local_counts[r];
        }
    }

    auto pack_owned = [&](const std::vector<double>& a) {
        std::vector<double> out(static_cast<size_t>(send_count));
        for (int li = 1; li <= d.local_n; ++li) {
            std::copy(&a[id(li, 0, N)], &a[id(li, 0, N)] + N, out.begin() + static_cast<size_t>(li - 1) * N);
        }
        return out;
    };

    std::vector<double> send_psi = pack_owned(psi);
    std::vector<double> send_omega = pack_owned(omega);
    std::vector<double> send_u = pack_owned(u);
    std::vector<double> send_v = pack_owned(v);

    std::vector<double> all_psi, all_omega, all_u, all_v;
    if (d.rank == 0) {
        all_psi.resize(static_cast<size_t>(N) * N);
        all_omega.resize(static_cast<size_t>(N) * N);
        all_u.resize(static_cast<size_t>(N) * N);
        all_v.resize(static_cast<size_t>(N) * N);
    }

    // Gatherv into rank order. Because row blocks are contiguous and assigned in rank order,
    // this is also global-row order for the current decomposition.
    MPI_Gatherv(send_psi.data(), send_count, MPI_DOUBLE, all_psi.data(), local_counts.data(), displs.data(), MPI_DOUBLE, 0, comm);
    MPI_Gatherv(send_omega.data(), send_count, MPI_DOUBLE, all_omega.data(), local_counts.data(), displs.data(), MPI_DOUBLE, 0, comm);
    MPI_Gatherv(send_u.data(), send_count, MPI_DOUBLE, all_u.data(), local_counts.data(), displs.data(), MPI_DOUBLE, 0, comm);
    MPI_Gatherv(send_v.data(), send_count, MPI_DOUBLE, all_v.data(), local_counts.data(), displs.data(), MPI_DOUBLE, 0, comm);

    if (d.rank == 0) {
        fs::create_directories(cfg.out_dir);
        std::ostringstream name;
        name << cfg.out_dir << "/cpp_hybrid_mpi_openmp_looped_N" << cfg.N << "_Re" << cfg.Re << "_" << cfg.scheme << "_fields.csv";
        std::ofstream out(name.str());
        out << std::setprecision(12);
        out << "i,j,x,y,u,v,psi,omega,speed\n";
        const double h = 1.0 / static_cast<double>(N - 1);
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                const size_t k = static_cast<size_t>(i) * N + j;
                const double speed = std::sqrt(all_u[k] * all_u[k] + all_v[k] * all_v[k]);
                out << i << ',' << j << ',' << j * h << ',' << i * h << ','
                    << all_u[k] << ',' << all_v[k] << ',' << all_psi[k] << ',' << all_omega[k] << ',' << speed << '\n';
            }
        }
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    try {
        Config cfg = parse_args(argc, argv);
        Decomp d = make_decomp(cfg.N, rank, size);

        if (d.local_n <= 0) {
            if (rank == 0) std::cerr << "Too many MPI ranks for N=" << cfg.N << '\n';
            MPI_Abort(MPI_COMM_WORLD, 2);
        }

        const int N = cfg.N;
        const double h = 1.0 / static_cast<double>(N - 1);
        const double nu = cfg.lid_velocity / static_cast<double>(cfg.Re);
        const double dt_diff = 0.20 * h * h / std::max(nu, 1e-12);

        std::vector<double> psi(static_cast<size_t>(d.local_n + 2) * N, 0.0);
        std::vector<double> omega(static_cast<size_t>(d.local_n + 2) * N, 0.0);
        std::vector<double> u(static_cast<size_t>(d.local_n + 2) * N, 0.0);
        std::vector<double> v(static_cast<size_t>(d.local_n + 2) * N, 0.0);

        apply_streamfunction_bc(psi, d, N);
        exchange_ghost_rows(psi, d, N, MPI_COMM_WORLD);
        apply_vorticity_bc(omega, psi, d, cfg);
        exchange_ghost_rows(omega, d, N, MPI_COMM_WORLD);

        double final_omega_change = std::numeric_limits<double>::infinity();
        double final_psi_change = std::numeric_limits<double>::infinity();
        double final_dt = 0.0;

        const double t0 = MPI_Wtime();

        for (int step = 1; step <= cfg.steps; ++step) {
            final_psi_change = solve_streamfunction_poisson(psi, omega, d, cfg, MPI_COMM_WORLD);
            const double local_umax = compute_velocity_and_max(psi, u, v, d, cfg);
            double global_umax = 0.0;
            MPI_Allreduce(&local_umax, &global_umax, 1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);
            const double dt_conv = cfg.cfl * h / std::max(global_umax, 1e-12);
            final_dt = std::min({cfg.max_dt, dt_conv, dt_diff});

            exchange_ghost_rows(omega, d, N, MPI_COMM_WORLD);
            const double local_omega_change = advance_vorticity(omega, u, v, d, cfg, final_dt);
            apply_vorticity_bc(omega, psi, d, cfg);
            exchange_ghost_rows(omega, d, N, MPI_COMM_WORLD);
            MPI_Allreduce(&local_omega_change, &final_omega_change, 1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);

            if (rank == 0 && (step == 1 || step % cfg.output_every == 0 || step == cfg.steps)) {
                std::cout << "step=" << step
                          << " dt=" << final_dt
                          << " psi_change=" << final_psi_change
                          << " omega_change=" << final_omega_change
                          << std::endl;
            }
        }

        final_psi_change = solve_streamfunction_poisson(psi, omega, d, cfg, MPI_COMM_WORLD);
        compute_velocity_and_max(psi, u, v, d, cfg);
        const double runtime = MPI_Wtime() - t0;

        if (cfg.write_fields) {
            gather_and_write_fields(psi, omega, u, v, d, cfg, MPI_COMM_WORLD);
        }

        if (rank == 0) {
            fs::create_directories(cfg.out_dir);
            std::ostringstream summary_path;
            summary_path << cfg.out_dir << "/cpp_hybrid_mpi_openmp_looped_summary.csv";
            const bool exists = fs::exists(summary_path.str());
            std::ofstream summary(summary_path.str(), std::ios::app);
            if (!exists) {
                summary << "Implementation,N,Re,Scheme,MPI_Ranks,OpenMP_Threads,Steps,PoissonIters,FinalDt,FinalPsiChange,FinalOmegaChange,Runtime_s,DomainDecomposition\n";
            }
            int threads = 1;
            #ifdef _OPENMP
            threads = omp_get_max_threads();
            #endif
            summary << "cpp_hybrid_mpi_openmp_looped," << cfg.N << ',' << cfg.Re << ',' << cfg.scheme << ','
                    << size << ',' << threads << ',' << cfg.steps << ',' << cfg.poisson_iters << ','
                    << final_dt << ',' << final_psi_change << ',' << final_omega_change << ','
                    << runtime << ",true\n";
            std::cout << "Hybrid MPI+OpenMP domain-decomposition run finished in " << runtime << " s\n";
            std::cout << "Summary: " << summary_path.str() << "\n";
        }
    } catch (const std::exception& e) {
        std::cerr << "[rank " << rank << "] error: " << e.what() << std::endl;
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    MPI_Finalize();
    return 0;
}
