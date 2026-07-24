#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace fs = std::filesystem;

constexpr double PI = 3.141592653589793238462643383279502884;

struct Matrix {
    int n{};
    std::vector<double> a;

    Matrix() = default;
    explicit Matrix(int n_, double value = 0.0) : n(n_), a(static_cast<size_t>(n_) * n_, value) {}

    double& operator()(int i, int j) { return a[static_cast<size_t>(i) * n + j]; }
    double operator()(int i, int j) const { return a[static_cast<size_t>(i) * n + j]; }
};

struct Config {
    double U_lid = 1.0;
    double L = 1.0;

    int maxIter = 4000;
    int maxIter_N128_bonus = 3000;
    int maxIter_Re1000_bonus = 3000;
    int maxIter_central_bonus = 1500;

    double tol_mass = 1e-7;
    double tol_divergence = 2e-3;
    double tol_velocity = 5e-7;
    double diverged_limit = 1e6;

    double cfl = 0.25;
    double dt_max = 0.0025;
    double dt_min = 1e-6;

    double alpha_u = 0.55;
    double alpha_p = 0.20;

    int poisson_maxIter = 2500;
    double poisson_tol_abs = 1e-8;
    double poisson_tol_rel = 1e-4;
    int poisson_check_every = 25;

    std::string sor_omega = "auto";
    double sor_omega_min = 1.15;
    double sor_omega_max = 1.90;

    std::vector<int> meshes = {32, 64, 128};
    std::vector<int> re_list = {100, 400, 1000};
    std::vector<std::string> schemes = {"upwind", "central"};
    std::vector<std::string> pressure_solvers = {"RBGS", "RBSOR"};
    std::vector<std::string> implementations = {"serial_cpp"};

    double validation_u_L2_limit_Re100 = 0.030;
    double validation_v_L2_limit_Re100 = 0.030;
    double validation_u_L2_limit_Re400 = 0.090;
    double validation_v_L2_limit_Re400 = 0.120;
    double validation_u_L2_limit_Re1000 = 0.160;
    double validation_v_L2_limit_Re1000 = 0.180;

    bool save_fields = true;
    bool paper_protocol = false;
    bool use_divergence_convergence = false;
    bool require_pressure_convergence = false;
    std::string results_dir = "results";
    std::string data_dir = "results/data";
};

struct PoissonInfo {
    int iter = 0;
    bool converged = false;
    double final_true_residual = std::numeric_limits<double>::infinity();
    double final_relative_residual = std::numeric_limits<double>::infinity();
    double final_change = std::numeric_limits<double>::infinity();
    double omega = 1.0;
    std::vector<double> residual_history;
    std::vector<double> change_history;
};

struct Result {
    int N = 0;
    int Re = 0;
    std::string scheme;
    std::string pressure_solver;
    std::string implementation;

    std::vector<double> x, y;
    Matrix u, v, p, speed, vorticity;

    // Ru/Rv and Rc_* remain for backward-compatible CSV consumers. They are
    // velocity-update and divergence-derived quantities, not true momentum residuals.
    std::vector<double> Ru, Rv, Rc_mass, Rc_div, dt, poisson_relative_residual;
    std::vector<int> poisson_iters;
    std::vector<bool> poisson_converged;

    int iterations = 0;
    int localMaxIter = 0;
    double runtime = 0.0;
    std::string status = "maxIter";
    bool execution_completed = false;
    bool outer_converged = false;
    bool final_pressure_converged = false;
    double final_poisson_relative_residual = std::numeric_limits<double>::infinity();
    double final_Ru = 0.0;
    double final_Rv = 0.0;
    double final_Rc_mass = 0.0;
    double final_Rc_div = 0.0;
    double avg_poisson_iters = 0.0;
    double avg_poisson_relative_residual = 0.0;
    double pressure_saturation_ratio = 0.0;
    int stagnation_counter = 0;
};

struct GhiaData {
    int Re = 0;
    std::vector<double> y_u, u, x_v, v;
};

struct Metrics {
    bool available = false;
    bool pass = false;
    double u_L2 = std::numeric_limits<double>::quiet_NaN();
    double v_L2 = std::numeric_limits<double>::quiet_NaN();
    double u_Linf = std::numeric_limits<double>::quiet_NaN();
    double v_Linf = std::numeric_limits<double>::quiet_NaN();
    double u_limit = std::numeric_limits<double>::quiet_NaN();
    double v_limit = std::numeric_limits<double>::quiet_NaN();
};

static std::string lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return static_cast<char>(std::tolower(c)); });
    return s;
}

static std::string upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

static std::string normalize_implementation(std::string s) {
    s = lower(s);
    // MATLAB has two implementations: vectorized and loop. This C++ package
    // intentionally contains one honest serial loop kernel. For convenience,
    // MATLAB labels are accepted as aliases, but CSV output uses serial_cpp.
    if (s == "serial" || s == "serial_cpp" || s == "cpp" || s == "loop" || s == "vectorized") {
        return "serial_cpp";
    }
    throw std::runtime_error("Unknown implementation: " + s + " (use serial_cpp)");
}

static double max_abs(const Matrix& m) {
    double r = 0.0;
    for (double v : m.a) r = std::max(r, std::abs(v));
    return r;
}

static double mean_all(const Matrix& m) {
    if (m.a.empty()) return 0.0;
    return std::accumulate(m.a.begin(), m.a.end(), 0.0) / static_cast<double>(m.a.size());
}

static bool all_finite(const Matrix& m) {
    for (double x : m.a) {
        if (!std::isfinite(x)) return false;
    }
    return true;
}
