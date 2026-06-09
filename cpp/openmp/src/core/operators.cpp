static void apply_lid_bc(Matrix& u, Matrix& v, double U_lid) {
    const int N = u.n;
    for (int j = 0; j < N; ++j) {
        u(0, j) = 0.0;         // bottom wall
        u(N - 1, j) = U_lid;   // moving lid
    }
    for (int i = 0; i < N; ++i) {
        u(i, 0) = 0.0;         // left wall; also sets top-left corner to zero
        u(i, N - 1) = 0.0;     // right wall; also sets top-right corner to zero
    }

    for (int j = 0; j < N; ++j) {
        v(0, j) = 0.0;
        v(N - 1, j) = 0.0;
    }
    for (int i = 0; i < N; ++i) {
        v(i, 0) = 0.0;
        v(i, N - 1) = 0.0;
    }
}

static void apply_pressure_bc(Matrix& p) {
    const int N = p.n;
    for (int i = 0; i < N; ++i) {
        p(i, 0) = p(i, 1);
        p(i, N - 1) = p(i, N - 2);
    }
    for (int j = 0; j < N; ++j) {
        p(0, j) = p(1, j);
        p(N - 1, j) = p(N - 2, j);
    }
    p(0, 0) = 0.0;
}

static double compute_dt(const Matrix& u, const Matrix& v, double dx, double dy, double nu, const Config& cfg) {
    const double max_vel = std::max({max_abs(u), max_abs(v), cfg.U_lid, 1e-12});
    const double h = std::min(dx, dy);
    const double dt_conv = cfg.cfl * h / max_vel;
    const double dt_diff = (nu > 0.0) ? 0.25 * h * h / nu : std::numeric_limits<double>::infinity();
    return std::min({dt_conv, dt_diff, cfg.dt_max});
}

static Matrix divergence_field(const Matrix& u, const Matrix& v, double dx, double dy) {
    const int N = u.n;
    Matrix div(N, 0.0);
    #pragma omp parallel for schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            div(i, j) = (u(i, j + 1) - u(i, j - 1)) / (2.0 * dx)
                      + (v(i + 1, j) - v(i - 1, j)) / (2.0 * dy);
        }
    }
    return div;
}

static Matrix compute_vorticity(const Matrix& u, const Matrix& v, double dx, double dy) {
    const int N = u.n;
    Matrix omega(N, 0.0);
    #pragma omp parallel for schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            omega(i, j) = (v(i, j + 1) - v(i, j - 1)) / (2.0 * dx)
                        - (u(i + 1, j) - u(i - 1, j)) / (2.0 * dy);
        }
    }
    return omega;
}

static std::tuple<Matrix, Matrix, double> momentum_predictor(
    const Matrix& u, const Matrix& v, const Matrix& p,
    int Re, const std::string& scheme_in, const Config& cfg
) {
    const int N = u.n;
    const double dx = cfg.L / static_cast<double>(N - 1);
    const double dy = dx;
    const double nu = cfg.U_lid * cfg.L / static_cast<double>(Re);
    const double dt = compute_dt(u, v, dx, dy, nu, cfg);
    const std::string scheme = lower(scheme_in);

    Matrix u_star = u;
    Matrix v_star = v;

    #pragma omp parallel for schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            const double uC = u(i, j);
            const double vC = v(i, j);

            const double lap_u = (u(i, j + 1) - 2.0 * u(i, j) + u(i, j - 1)) / (dx * dx)
                               + (u(i + 1, j) - 2.0 * u(i, j) + u(i - 1, j)) / (dy * dy);
            const double lap_v = (v(i, j + 1) - 2.0 * v(i, j) + v(i, j - 1)) / (dx * dx)
                               + (v(i + 1, j) - 2.0 * v(i, j) + v(i - 1, j)) / (dy * dy);

            double du_dx, du_dy, dv_dx, dv_dy;

            if (scheme == "central") {
                du_dx = (u(i, j + 1) - u(i, j - 1)) / (2.0 * dx);
                du_dy = (u(i + 1, j) - u(i - 1, j)) / (2.0 * dy);
                dv_dx = (v(i, j + 1) - v(i, j - 1)) / (2.0 * dx);
                dv_dy = (v(i + 1, j) - v(i - 1, j)) / (2.0 * dy);
            } else if (scheme == "upwind") {
                if (uC >= 0.0) {
                    du_dx = (u(i, j) - u(i, j - 1)) / dx;
                    dv_dx = (v(i, j) - v(i, j - 1)) / dx;
                } else {
                    du_dx = (u(i, j + 1) - u(i, j)) / dx;
                    dv_dx = (v(i, j + 1) - v(i, j)) / dx;
                }

                if (vC >= 0.0) {
                    du_dy = (u(i, j) - u(i - 1, j)) / dy;
                    dv_dy = (v(i, j) - v(i - 1, j)) / dy;
                } else {
                    du_dy = (u(i + 1, j) - u(i, j)) / dy;
                    dv_dy = (v(i + 1, j) - v(i, j)) / dy;
                }
            } else {
                throw std::runtime_error("Unknown convection scheme: " + scheme_in);
            }

            const double conv_u = uC * du_dx + vC * du_dy;
            const double conv_v = uC * dv_dx + vC * dv_dy;
            const double dp_dx = (p(i, j + 1) - p(i, j - 1)) / (2.0 * dx);
            const double dp_dy = (p(i + 1, j) - p(i - 1, j)) / (2.0 * dy);

            const double u_pred = u(i, j) + dt * (-conv_u - dp_dx + nu * lap_u);
            const double v_pred = v(i, j) + dt * (-conv_v - dp_dy + nu * lap_v);

            u_star(i, j) = (1.0 - cfg.alpha_u) * u(i, j) + cfg.alpha_u * u_pred;
            v_star(i, j) = (1.0 - cfg.alpha_u) * v(i, j) + cfg.alpha_u * v_pred;
        }
    }

    apply_lid_bc(u_star, v_star, cfg.U_lid);
    return {u_star, v_star, dt};
}

static double poisson_true_residual(const Matrix& phi, const Matrix& rhs, double dx, double dy) {
    const int N = phi.n;
    double res = 0.0;
#pragma omp parallel for reduction(max:res) schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            const double lap = (phi(i, j + 1) - 2.0 * phi(i, j) + phi(i, j - 1)) / (dx * dx)
                             + (phi(i + 1, j) - 2.0 * phi(i, j) + phi(i - 1, j)) / (dy * dy);
            res = std::max(res, std::abs(lap - rhs(i, j)));
        }
    }
    return res;
}

static std::tuple<Matrix, PoissonInfo> pressure_poisson(
    const Matrix& rhs, double dx, double dy, const std::string& solver_type_in, const Config& cfg
) {
    const int N = rhs.n;
    Matrix phi(N, 0.0);
    Matrix rhs2 = rhs;
    const std::string solver_type = upper(solver_type_in);

    double interior_sum = 0.0;
    int count = 0;
#pragma omp parallel for reduction(+:interior_sum,count) schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            interior_sum += rhs2(i, j);
            ++count;
        }
    }
    const double interior_mean = (count > 0) ? interior_sum / static_cast<double>(count) : 0.0;
    #pragma omp parallel for schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            rhs2(i, j) -= interior_mean;
        }
    }

    const double den = 2.0 * (dx * dx + dy * dy);
    double omega;
    if (lower(cfg.sor_omega) == "auto") {
        omega = 2.0 / (1.0 + std::sin(PI / static_cast<double>(N - 1)));
        omega = std::min(std::max(omega, cfg.sor_omega_min), cfg.sor_omega_max);
    } else {
        omega = std::stod(cfg.sor_omega);
    }

    double rhs_norm = 1.0;
#pragma omp parallel for reduction(max:rhs_norm) schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            rhs_norm = std::max(rhs_norm, std::abs(rhs2(i, j)));
        }
    }

    PoissonInfo info;
    info.omega = omega;
    info.residual_history.assign(static_cast<size_t>(cfg.poisson_maxIter), 0.0);
    info.change_history.assign(static_cast<size_t>(cfg.poisson_maxIter), 0.0);

    bool converged = false;
    double final_res = std::numeric_limits<double>::infinity();
    double final_change = std::numeric_limits<double>::infinity();
    int it = 0;

    for (it = 1; it <= cfg.poisson_maxIter; ++it) {
        Matrix phi_old = phi;

        if (solver_type == "JACOBI") {
            Matrix phi_new = phi;
            #pragma omp parallel for schedule(static)
            for (int i = 1; i < N - 1; ++i) {
                for (int j = 1; j < N - 1; ++j) {
                    phi_new(i, j) = ((phi(i + 1, j) + phi(i - 1, j)) * dy * dy
                                   + (phi(i, j + 1) + phi(i, j - 1)) * dx * dx
                                   - rhs2(i, j) * dx * dx * dy * dy) / den;
                }
            }
            phi = std::move(phi_new);
            apply_pressure_bc(phi);
        } else if (solver_type == "RBGS" || solver_type == "RBSOR") {
            for (int color = 0; color <= 1; ++color) {
                #pragma omp parallel for schedule(static)
                for (int i = 1; i < N - 1; ++i) {
                    for (int j = 1; j < N - 1; ++j) {
                        const bool is_red = ((i + 1) + (j + 1)) % 2 == 0; // MATLAB i+j parity
                        if ((color == 0 && !is_red) || (color == 1 && is_red)) continue;

                        const double candidate = ((phi(i + 1, j) + phi(i - 1, j)) * dy * dy
                                                + (phi(i, j + 1) + phi(i, j - 1)) * dx * dx
                                                - rhs2(i, j) * dx * dx * dy * dy) / den;
                        if (solver_type == "RBSOR") {
                            phi(i, j) = (1.0 - omega) * phi(i, j) + omega * candidate;
                        } else {
                            phi(i, j) = candidate;
                        }
                    }
                }
                apply_pressure_bc(phi);
            }
        } else {
            throw std::runtime_error("Unknown pressure solver: " + solver_type_in);
        }

        final_change = 0.0;
#pragma omp parallel for reduction(max:final_change) schedule(static)
        for (long long k = 0; k < static_cast<long long>(phi.a.size()); ++k) {
            const size_t kk = static_cast<size_t>(k);
            final_change = std::max(final_change, std::abs(phi.a[kk] - phi_old.a[kk]));
        }
        info.change_history[static_cast<size_t>(it - 1)] = final_change;

        if ((it % cfg.poisson_check_every) == 0 || it == 1 || it == cfg.poisson_maxIter) {
            final_res = poisson_true_residual(phi, rhs2, dx, dy);
            const double rel_res = final_res / rhs_norm;
            info.residual_history[static_cast<size_t>(it - 1)] = rel_res;
            if (final_res < cfg.poisson_tol_abs || rel_res < cfg.poisson_tol_rel) {
                converged = true;
                break;
            }
        }
    }

    if (it > cfg.poisson_maxIter) {
        it = cfg.poisson_maxIter;
    }

    if (!converged) {
        final_res = poisson_true_residual(phi, rhs2, dx, dy);
    }

    info.iter = it;
    info.converged = converged;
    info.final_true_residual = final_res;
    info.final_relative_residual = final_res / rhs_norm;
    info.final_change = final_change;
    info.residual_history.resize(static_cast<size_t>(it));
    info.change_history.resize(static_cast<size_t>(it));
    return {phi, info};
}

static std::tuple<double, double, double, double> velocity_residuals(
    const Matrix& u, const Matrix& v, const Matrix& u_old, const Matrix& v_old,
    double dx, double dy, double U, double L
) {
    double Ru = 0.0;
    double Rv = 0.0;
    for (size_t k = 0; k < u.a.size(); ++k) {
        Ru = std::max(Ru, std::abs(u.a[k] - u_old.a[k]));
        Rv = std::max(Rv, std::abs(v.a[k] - v_old.a[k]));
    }

    Matrix div = divergence_field(u, v, dx, dy);
    const double Rc_div = max_abs(div);
    const double scale = std::max(U * L, std::numeric_limits<double>::epsilon());
    const double Rc_mass = Rc_div * dx * dy / scale;
    return {Ru, Rv, Rc_mass, Rc_div};
}

