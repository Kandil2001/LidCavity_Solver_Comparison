static Result solve_lid_cavity(int N, int Re, std::string scheme, std::string pressure_solver, std::string implementation, const Config& cfg) {
    scheme = lower(scheme);
    pressure_solver = upper(pressure_solver);
    implementation = normalize_implementation(implementation);

    const double dx = cfg.L / static_cast<double>(N - 1);
    const double dy = dx;

    int localMaxIter = cfg.maxIter;
    if (N >= 128) localMaxIter += cfg.maxIter_N128_bonus;
    if (Re >= 1000) localMaxIter += cfg.maxIter_Re1000_bonus;
    if (scheme == "central") localMaxIter += cfg.maxIter_central_bonus;

    Matrix u(N, 0.0), v(N, 0.0), p(N, 0.0);
    apply_lid_bc(u, v, cfg.U_lid);

    Result result;
    result.N = N;
    result.Re = Re;
    result.scheme = scheme;
    result.pressure_solver = pressure_solver;
    result.implementation = implementation;
    result.localMaxIter = localMaxIter;

    result.Ru.reserve(localMaxIter);
    result.Rv.reserve(localMaxIter);
    result.Rc_mass.reserve(localMaxIter);
    result.Rc_div.reserve(localMaxIter);
    result.dt.reserve(localMaxIter);
    result.poisson_iters.reserve(localMaxIter);
    result.poisson_relative_residual.reserve(localMaxIter);
    result.poisson_converged.reserve(localMaxIter);

    std::string status = "maxIter";
    int stagnation_counter = 0;
    double prev_mass = std::numeric_limits<double>::infinity();
    int iter = 0;

    const auto t0 = std::chrono::steady_clock::now();

    for (iter = 1; iter <= localMaxIter; ++iter) {
        Matrix u_old = u;
        Matrix v_old = v;

        auto [u_star, v_star, dt] = momentum_predictor(u, v, p, Re, scheme, cfg);
        dt = std::max(dt, cfg.dt_min);

        Matrix div_star = divergence_field(u_star, v_star, dx, dy);
        Matrix rhs(N, 0.0);
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                rhs(i, j) = div_star(i, j) / dt;
            }
        }

        auto [p_prime, pinfo] = pressure_poisson(rhs, dx, dy, pressure_solver, cfg);

        u = u_star;
        v = v_star;
        #pragma omp parallel for schedule(static)
        for (int i = 1; i < N - 1; ++i) {
            for (int j = 1; j < N - 1; ++j) {
                const double dpdx = (p_prime(i, j + 1) - p_prime(i, j - 1)) / (2.0 * dx);
                const double dpdy = (p_prime(i + 1, j) - p_prime(i - 1, j)) / (2.0 * dy);
                u(i, j) = u_star(i, j) - dt * dpdx;
                v(i, j) = v_star(i, j) - dt * dpdy;
            }
        }

        for (size_t k = 0; k < p.a.size(); ++k) {
            p.a[k] += cfg.alpha_p * p_prime.a[k];
        }
        const double p_mean = mean_all(p);
        #pragma omp parallel for schedule(static)
        for (long long k = 0; k < static_cast<long long>(p.a.size()); ++k) p.a[static_cast<size_t>(k)] -= p_mean;

        apply_lid_bc(u, v, cfg.U_lid);

        auto [Ru, Rv, Rc_mass, Rc_div] = velocity_residuals(u, v, u_old, v_old, dx, dy, cfg.U_lid, cfg.L);
        result.Ru.push_back(Ru);
        result.Rv.push_back(Rv);
        result.Rc_mass.push_back(Rc_mass);
        result.Rc_div.push_back(Rc_div);
        result.dt.push_back(dt);
        result.poisson_iters.push_back(pinfo.iter);
        result.poisson_relative_residual.push_back(pinfo.final_relative_residual);
        result.poisson_converged.push_back(pinfo.converged);

        if (!all_finite(u) || !all_finite(v) || !all_finite(p) || std::max({Ru, Rv, Rc_div}) > cfg.diverged_limit) {
            status = "diverged";
            break;
        }

        if (Rc_mass > 0.995 * prev_mass) {
            ++stagnation_counter;
        } else {
            stagnation_counter = 0;
        }
        prev_mass = Rc_mass;

        if (Rc_mass < cfg.tol_mass && std::max(Ru, Rv) < cfg.tol_velocity) {
            status = "converged";
            break;
        }
    }

    if (iter > localMaxIter) {
        iter = localMaxIter;
    }

    const auto t1 = std::chrono::steady_clock::now();
    result.runtime = std::chrono::duration<double>(t1 - t0).count();

    result.iterations = iter;
    result.status = status;
    result.stagnation_counter = stagnation_counter;

    result.x.resize(N);
    result.y.resize(N);
    for (int k = 0; k < N; ++k) {
        result.x[k] = static_cast<double>(k) * cfg.L / static_cast<double>(N - 1);
        result.y[k] = result.x[k];
    }

    result.u = std::move(u);
    result.v = std::move(v);
    result.p = std::move(p);
    result.speed = Matrix(N, 0.0);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            result.speed(i, j) = std::sqrt(result.u(i, j) * result.u(i, j) + result.v(i, j) * result.v(i, j));
        }
    }
    result.vorticity = compute_vorticity(result.u, result.v, dx, dy);

    result.final_Ru = result.Ru.empty() ? 0.0 : result.Ru.back();
    result.final_Rv = result.Rv.empty() ? 0.0 : result.Rv.back();
    result.final_Rc_mass = result.Rc_mass.empty() ? 0.0 : result.Rc_mass.back();
    result.final_Rc_div = result.Rc_div.empty() ? 0.0 : result.Rc_div.back();

    if (!result.poisson_iters.empty()) {
        result.avg_poisson_iters = std::accumulate(result.poisson_iters.begin(), result.poisson_iters.end(), 0.0)
                                 / static_cast<double>(result.poisson_iters.size());
        result.avg_poisson_relative_residual = std::accumulate(result.poisson_relative_residual.begin(), result.poisson_relative_residual.end(), 0.0)
                                            / static_cast<double>(result.poisson_relative_residual.size());
        int saturated = 0;
        for (int pi : result.poisson_iters) if (pi >= cfg.poisson_maxIter) ++saturated;
        result.pressure_saturation_ratio = static_cast<double>(saturated) / static_cast<double>(result.poisson_iters.size());
    }

    return result;
}

