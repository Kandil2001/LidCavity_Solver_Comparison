/* -------------------------------------------------------------------------
 * Main SIMPLE-style solver
 * ------------------------------------------------------------------------- */

static Result solve_lid_cavity(int N, int Re, const char *scheme_in, const char *pressure_solver_in, const char *implementation_in, const Config *cfg) {
    char scheme[32]; strlower_copy(scheme, scheme_in, sizeof(scheme));
    char pressure_solver[32]; strupper_copy(pressure_solver, pressure_solver_in, sizeof(pressure_solver));
    char implementation[32];
    normalize_c_implementation(implementation, implementation_in, sizeof(implementation));

    double dx = cfg->L / (double)(N - 1);
    double dy = dx;
    int localMaxIter = cfg->maxIter;
    if (N >= 128) localMaxIter += cfg->maxIter_N128_bonus;
    if (Re >= 1000) localMaxIter += cfg->maxIter_Re1000_bonus;
    if (strcmp(scheme, "central") == 0) localMaxIter += cfg->maxIter_central_bonus;

    Matrix u = matrix_new(N, 0.0);
    Matrix v = matrix_new(N, 0.0);
    Matrix p = matrix_new(N, 0.0);
    apply_lid_bc(&u, &v, cfg->U_lid);

    Result r;
    memset(&r, 0, sizeof(Result));
    r.N = N;
    r.Re = Re;
    snprintf(r.scheme, sizeof(r.scheme), "%s", scheme);
    snprintf(r.pressure_solver, sizeof(r.pressure_solver), "%s", pressure_solver);
    snprintf(r.implementation, sizeof(r.implementation), "%s", implementation);
    r.localMaxIter = localMaxIter;
    snprintf(r.status, sizeof(r.status), "maxIter");
    r.hist_cap = localMaxIter;
    r.Ru = (double*)malloc((size_t)localMaxIter * sizeof(double));
    r.Rv = (double*)malloc((size_t)localMaxIter * sizeof(double));
    r.Rc_mass = (double*)malloc((size_t)localMaxIter * sizeof(double));
    r.Rc_div = (double*)malloc((size_t)localMaxIter * sizeof(double));
    r.dt = (double*)malloc((size_t)localMaxIter * sizeof(double));
    r.poisson_iters = (int*)malloc((size_t)localMaxIter * sizeof(int));
    r.poisson_relative_residual = (double*)malloc((size_t)localMaxIter * sizeof(double));
    r.poisson_converged = (int*)malloc((size_t)localMaxIter * sizeof(int));
    if (!r.Ru || !r.Rv || !r.Rc_mass || !r.Rc_div || !r.dt || !r.poisson_iters || !r.poisson_relative_residual || !r.poisson_converged) die("Out of memory");

    int stagnation_counter = 0;
    double prev_mass = DBL_MAX;
    int iter = 0;
    double t0 = wall_time();

    for (iter = 1; iter <= localMaxIter; ++iter) {
        Matrix u_old = matrix_copy(&u);
        Matrix v_old = matrix_copy(&v);
        Matrix u_star, v_star;
        double dt;
        momentum_predictor(&u, &v, &p, Re, scheme, cfg, &u_star, &v_star, &dt);
        if (dt < cfg->dt_min) dt = cfg->dt_min;

        Matrix div_star = divergence_field(&u_star, &v_star, dx, dy);
        Matrix rhs = matrix_new(N, 0.0);
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                AT(rhs, i, j) = AT(div_star, i, j) / dt;
            }
        }
        matrix_free(&div_star);

        PoissonInfo pinfo;
        Matrix p_prime = pressure_poisson(&rhs, dx, dy, pressure_solver, cfg, &pinfo);
        matrix_free(&rhs);

        matrix_free(&u);
        matrix_free(&v);
        u = matrix_copy(&u_star);
        v = matrix_copy(&v_star);
        #pragma omp parallel for schedule(static)
        for (int i = 1; i < N - 1; ++i) {
            for (int j = 1; j < N - 1; ++j) {
                double dpdx = (AT(p_prime, i, j + 1) - AT(p_prime, i, j - 1)) / (2.0 * dx);
                double dpdy = (AT(p_prime, i + 1, j) - AT(p_prime, i - 1, j)) / (2.0 * dy);
                AT(u, i, j) = AT(u_star, i, j) - dt * dpdx;
                AT(v, i, j) = AT(v_star, i, j) - dt * dpdy;
            }
        }

        int nn = N * N;
        #pragma omp parallel for schedule(static)
        for (int k = 0; k < nn; ++k) p.a[k] += cfg->alpha_p * p_prime.a[k];
        double p_mean = mean_matrix(&p);
        #pragma omp parallel for schedule(static)
        for (int k = 0; k < nn; ++k) p.a[k] -= p_mean;
        apply_lid_bc(&u, &v, cfg->U_lid);

        double Ru, Rv, Rc_mass, Rc_div;
        velocity_residuals(&u, &v, &u_old, &v_old, dx, dy, cfg->U_lid, cfg->L, &Ru, &Rv, &Rc_mass, &Rc_div);
        int k = r.hist_count++;
        r.Ru[k] = Ru;
        r.Rv[k] = Rv;
        r.Rc_mass[k] = Rc_mass;
        r.Rc_div[k] = Rc_div;
        r.dt[k] = dt;
        r.poisson_iters[k] = pinfo.iter;
        r.poisson_relative_residual[k] = pinfo.final_relative_residual;
        r.poisson_converged[k] = pinfo.converged;

        matrix_free(&u_old);
        matrix_free(&v_old);
        matrix_free(&u_star);
        matrix_free(&v_star);
        matrix_free(&p_prime);

        double max_r = Ru;
        if (Rv > max_r) max_r = Rv;
        if (Rc_div > max_r) max_r = Rc_div;
        if (!all_finite_matrix(&u) || !all_finite_matrix(&v) || !all_finite_matrix(&p) || max_r > cfg->diverged_limit) {
            snprintf(r.status, sizeof(r.status), "diverged");
            break;
        }
        if (Rc_mass > 0.995 * prev_mass) ++stagnation_counter; else stagnation_counter = 0;
        prev_mass = Rc_mass;
        if (Rc_mass < cfg->tol_mass && (Ru > Rv ? Ru : Rv) < cfg->tol_velocity) {
            snprintf(r.status, sizeof(r.status), "converged");
            break;
        }
    }
    if (iter > localMaxIter) iter = localMaxIter;
    r.runtime = wall_time() - t0;
    r.iterations = iter;
    r.stagnation_counter = stagnation_counter;

    r.x = (double*)malloc((size_t)N * sizeof(double));
    r.y = (double*)malloc((size_t)N * sizeof(double));
    if (!r.x || !r.y) die("Out of memory");
    for (int k = 0; k < N; ++k) {
        r.x[k] = (double)k * cfg->L / (double)(N - 1);
        r.y[k] = r.x[k];
    }
    r.u = u;
    r.v = v;
    r.p = p;
    r.speed = matrix_new(N, 0.0);
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            double uu = AT(r.u, i, j), vv = AT(r.v, i, j);
            AT(r.speed, i, j) = sqrt(uu * uu + vv * vv);
        }
    }
    r.vorticity = compute_vorticity(&r.u, &r.v, dx, dy);

    r.final_Ru = r.hist_count ? r.Ru[r.hist_count - 1] : 0.0;
    r.final_Rv = r.hist_count ? r.Rv[r.hist_count - 1] : 0.0;
    r.final_Rc_mass = r.hist_count ? r.Rc_mass[r.hist_count - 1] : 0.0;
    r.final_Rc_div = r.hist_count ? r.Rc_div[r.hist_count - 1] : 0.0;
    if (r.hist_count) {
        double spi = 0.0, spr = 0.0;
        int saturated = 0;
        for (int k = 0; k < r.hist_count; ++k) {
            spi += (double)r.poisson_iters[k];
            spr += r.poisson_relative_residual[k];
            if (r.poisson_iters[k] >= cfg->poisson_maxIter) ++saturated;
        }
        r.avg_poisson_iters = spi / (double)r.hist_count;
        r.avg_poisson_relative_residual = spr / (double)r.hist_count;
        r.pressure_saturation_ratio = (double)saturated / (double)r.hist_count;
    }
    return r;
}

static void free_result(Result *r) {
    free(r->x); free(r->y);
    matrix_free(&r->u); matrix_free(&r->v); matrix_free(&r->p); matrix_free(&r->speed); matrix_free(&r->vorticity);
    free(r->Ru); free(r->Rv); free(r->Rc_mass); free(r->Rc_div); free(r->dt);
    free(r->poisson_iters); free(r->poisson_relative_residual); free(r->poisson_converged);
    memset(r, 0, sizeof(Result));
}

