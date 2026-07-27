/* -------------------------------------------------------------------------
 * CFD operators and boundary conditions
 * ------------------------------------------------------------------------- */

static void apply_lid_bc(Matrix *u, Matrix *v, double U_lid) {
    int N = u->n;
    for (int j = 0; j < N; ++j) {
        AT((*u), 0, j) = 0.0;
        AT((*u), N - 1, j) = U_lid;
    }
    for (int i = 0; i < N; ++i) {
        AT((*u), i, 0) = 0.0;
        AT((*u), i, N - 1) = 0.0;
    }
    for (int j = 0; j < N; ++j) {
        AT((*v), 0, j) = 0.0;
        AT((*v), N - 1, j) = 0.0;
    }
    for (int i = 0; i < N; ++i) {
        AT((*v), i, 0) = 0.0;
        AT((*v), i, N - 1) = 0.0;
    }
}

static void apply_pressure_bc(Matrix *p) {
    int N = p->n;
    for (int i = 0; i < N; ++i) {
        AT((*p), i, 0) = AT((*p), i, 1);
        AT((*p), i, N - 1) = AT((*p), i, N - 2);
    }
    for (int j = 0; j < N; ++j) {
        AT((*p), 0, j) = AT((*p), 1, j);
        AT((*p), N - 1, j) = AT((*p), N - 2, j);
    }
    AT((*p), 0, 0) = 0.0;
}

static double compute_dt(const Matrix *u, const Matrix *v, double dx, double dy, double nu, const Config *cfg) {
    double max_vel = max_abs_matrix(u);
    double mv = max_abs_matrix(v);
    if (mv > max_vel) max_vel = mv;
    if (cfg->U_lid > max_vel) max_vel = cfg->U_lid;
    if (max_vel < 1e-12) max_vel = 1e-12;
    double h = dx < dy ? dx : dy;
    double dt_conv = cfg->cfl * h / max_vel;
    double dt_diff = nu > 0.0 ? 0.25 * h * h / nu : DBL_MAX;
    double out = dt_conv;
    if (dt_diff < out) out = dt_diff;
    if (cfg->dt_max < out) out = cfg->dt_max;
    return out;
}

static Matrix divergence_field(const Matrix *u, const Matrix *v, double dx, double dy) {
    int N = u->n;
    Matrix div = matrix_new(N, 0.0);
    #pragma omp parallel for schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            AT(div, i, j) = (AT((*u), i, j + 1) - AT((*u), i, j - 1)) / (2.0 * dx)
                         + (AT((*v), i + 1, j) - AT((*v), i - 1, j)) / (2.0 * dy);
        }
    }
    return div;
}

static Matrix compute_vorticity(const Matrix *u, const Matrix *v, double dx, double dy) {
    int N = u->n;
    Matrix omega = matrix_new(N, 0.0);
    #pragma omp parallel for schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            AT(omega, i, j) = (AT((*v), i, j + 1) - AT((*v), i, j - 1)) / (2.0 * dx)
                           - (AT((*u), i + 1, j) - AT((*u), i - 1, j)) / (2.0 * dy);
        }
    }
    return omega;
}

static void momentum_predictor(const Matrix *u, const Matrix *v, const Matrix *p,
                               int Re, const char *scheme_in, const Config *cfg,
                               Matrix *u_star, Matrix *v_star, double *dt_out) {
    int N = u->n;
    double dx = cfg->L / (double)(N - 1);
    double dy = dx;
    double nu = cfg->U_lid * cfg->L / (double)Re;
    double dt = compute_dt(u, v, dx, dy, nu, cfg);
    char scheme[32]; strlower_copy(scheme, scheme_in, sizeof(scheme));

    *u_star = matrix_copy(u);
    *v_star = matrix_copy(v);

    #pragma omp parallel for schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            double uC = AT((*u), i, j);
            double vC = AT((*v), i, j);
            double lap_u = (AT((*u), i, j + 1) - 2.0 * AT((*u), i, j) + AT((*u), i, j - 1)) / (dx * dx)
                         + (AT((*u), i + 1, j) - 2.0 * AT((*u), i, j) + AT((*u), i - 1, j)) / (dy * dy);
            double lap_v = (AT((*v), i, j + 1) - 2.0 * AT((*v), i, j) + AT((*v), i, j - 1)) / (dx * dx)
                         + (AT((*v), i + 1, j) - 2.0 * AT((*v), i, j) + AT((*v), i - 1, j)) / (dy * dy);
            double du_dx, du_dy, dv_dx, dv_dy;
            if (strcmp(scheme, "central") == 0) {
                du_dx = (AT((*u), i, j + 1) - AT((*u), i, j - 1)) / (2.0 * dx);
                du_dy = (AT((*u), i + 1, j) - AT((*u), i - 1, j)) / (2.0 * dy);
                dv_dx = (AT((*v), i, j + 1) - AT((*v), i, j - 1)) / (2.0 * dx);
                dv_dy = (AT((*v), i + 1, j) - AT((*v), i - 1, j)) / (2.0 * dy);
            } else if (strcmp(scheme, "upwind") == 0) {
                if (uC >= 0.0) {
                    du_dx = (AT((*u), i, j) - AT((*u), i, j - 1)) / dx;
                    dv_dx = (AT((*v), i, j) - AT((*v), i, j - 1)) / dx;
                } else {
                    du_dx = (AT((*u), i, j + 1) - AT((*u), i, j)) / dx;
                    dv_dx = (AT((*v), i, j + 1) - AT((*v), i, j)) / dx;
                }
                if (vC >= 0.0) {
                    du_dy = (AT((*u), i, j) - AT((*u), i - 1, j)) / dy;
                    dv_dy = (AT((*v), i, j) - AT((*v), i - 1, j)) / dy;
                } else {
                    du_dy = (AT((*u), i + 1, j) - AT((*u), i, j)) / dy;
                    dv_dy = (AT((*v), i + 1, j) - AT((*v), i, j)) / dy;
                }
            } else {
                die("Unknown convection scheme");
            }
            double conv_u = uC * du_dx + vC * du_dy;
            double conv_v = uC * dv_dx + vC * dv_dy;
            double dp_dx = (AT((*p), i, j + 1) - AT((*p), i, j - 1)) / (2.0 * dx);
            double dp_dy = (AT((*p), i + 1, j) - AT((*p), i - 1, j)) / (2.0 * dy);
            double u_pred = AT((*u), i, j) + dt * (-conv_u - dp_dx + nu * lap_u);
            double v_pred = AT((*v), i, j) + dt * (-conv_v - dp_dy + nu * lap_v);
            AT((*u_star), i, j) = (1.0 - cfg->alpha_u) * AT((*u), i, j) + cfg->alpha_u * u_pred;
            AT((*v_star), i, j) = (1.0 - cfg->alpha_u) * AT((*v), i, j) + cfg->alpha_u * v_pred;
        }
    }
    apply_lid_bc(u_star, v_star, cfg->U_lid);
    *dt_out = dt;
}

static double poisson_true_residual(const Matrix *phi, const Matrix *rhs, double dx, double dy) {
    int N = phi->n;
    double res = 0.0;
    #pragma omp parallel for reduction(max:res) schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            double lap = (AT((*phi), i, j + 1) - 2.0 * AT((*phi), i, j) + AT((*phi), i, j - 1)) / (dx * dx)
                       + (AT((*phi), i + 1, j) - 2.0 * AT((*phi), i, j) + AT((*phi), i - 1, j)) / (dy * dy);
            double e = fabs(lap - AT((*rhs), i, j));
            if (e > res) res = e;
        }
    }
    return res;
}

static Matrix pressure_poisson(const Matrix *rhs, double dx, double dy, const char *solver_type_in, const Config *cfg, PoissonInfo *info) {
    int N = rhs->n;
    Matrix phi = matrix_new(N, 0.0);
    Matrix rhs2 = matrix_copy(rhs);
    char solver_type[32]; strupper_copy(solver_type, solver_type_in, sizeof(solver_type));

    double interior_sum = 0.0;
    int count = 0;
    #pragma omp parallel for reduction(+:interior_sum,count) schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            interior_sum += AT(rhs2, i, j);
            ++count;
        }
    }
    double interior_mean = count > 0 ? interior_sum / (double)count : 0.0;
    #pragma omp parallel for schedule(static)
    for (int i = 1; i < N - 1; ++i)
        for (int j = 1; j < N - 1; ++j)
            AT(rhs2, i, j) -= interior_mean;

    double den = 2.0 * (dx * dx + dy * dy);
    double omega;
    char sor[32]; strlower_copy(sor, cfg->sor_omega, sizeof(sor));
    if (strcmp(sor, "auto") == 0) {
        omega = 2.0 / (1.0 + sin(M_PI / (double)(N - 1)));
        if (omega < cfg->sor_omega_min) omega = cfg->sor_omega_min;
        if (omega > cfg->sor_omega_max) omega = cfg->sor_omega_max;
    } else {
        omega = atof(cfg->sor_omega);
    }

    double rhs_norm = 1.0;
    #pragma omp parallel for reduction(max:rhs_norm) schedule(static)
    for (int i = 1; i < N - 1; ++i) {
        for (int j = 1; j < N - 1; ++j) {
            double v = fabs(AT(rhs2, i, j));
            if (v > rhs_norm) rhs_norm = v;
        }
    }

    int converged = 0;
    double final_res = DBL_MAX;
    double final_change = DBL_MAX;
    int it = 0;

    for (it = 1; it <= cfg->poisson_maxIter; ++it) {
        Matrix phi_old = matrix_copy(&phi);

        if (strcmp(solver_type, "JACOBI") == 0) {
            Matrix phi_new = matrix_copy(&phi);
            #pragma omp parallel for schedule(static)
            for (int i = 1; i < N - 1; ++i) {
                for (int j = 1; j < N - 1; ++j) {
                    AT(phi_new, i, j) = ((AT(phi, i + 1, j) + AT(phi, i - 1, j)) * dy * dy
                                      + (AT(phi, i, j + 1) + AT(phi, i, j - 1)) * dx * dx
                                      - AT(rhs2, i, j) * dx * dx * dy * dy) / den;
                }
            }
            matrix_free(&phi);
            phi = phi_new;
            apply_pressure_bc(&phi);
        } else if (strcmp(solver_type, "RBGS") == 0 || strcmp(solver_type, "RBSOR") == 0) {
            for (int color = 0; color <= 1; ++color) {
                #pragma omp parallel for schedule(static)
                for (int i = 1; i < N - 1; ++i) {
                    for (int j = 1; j < N - 1; ++j) {
                        int is_red = (((i + 1) + (j + 1)) % 2) == 0;
                        if ((color == 0 && !is_red) || (color == 1 && is_red)) continue;
                        double candidate = ((AT(phi, i + 1, j) + AT(phi, i - 1, j)) * dy * dy
                                          + (AT(phi, i, j + 1) + AT(phi, i, j - 1)) * dx * dx
                                          - AT(rhs2, i, j) * dx * dx * dy * dy) / den;
                        if (strcmp(solver_type, "RBSOR") == 0) {
                            AT(phi, i, j) = (1.0 - omega) * AT(phi, i, j) + omega * candidate;
                        } else {
                            AT(phi, i, j) = candidate;
                        }
                    }
                }
                apply_pressure_bc(&phi);
            }
        } else {
            die("Unknown pressure solver");
        }

        final_change = 0.0;
        int nn = N * N;
        #pragma omp parallel for reduction(max:final_change) schedule(static)
        for (int k = 0; k < nn; ++k) {
            double c = fabs(phi.a[k] - phi_old.a[k]);
            if (c > final_change) final_change = c;
        }
        matrix_free(&phi_old);

        if ((it % cfg->poisson_check_every) == 0 || it == 1 || it == cfg->poisson_maxIter) {
            final_res = poisson_true_residual(&phi, &rhs2, dx, dy);
            double rel_res = final_res / rhs_norm;
            if (final_res < cfg->poisson_tol_abs || rel_res < cfg->poisson_tol_rel) {
                converged = 1;
                break;
            }
        }
    }
    if (it > cfg->poisson_maxIter) it = cfg->poisson_maxIter;
    if (!converged) final_res = poisson_true_residual(&phi, &rhs2, dx, dy);

    info->iter = it;
    info->converged = converged;
    info->final_true_residual = final_res;
    info->final_relative_residual = final_res / rhs_norm;
    info->final_change = final_change;
    info->omega = omega;

    matrix_free(&rhs2);
    return phi;
}

static void velocity_residuals(const Matrix *u, const Matrix *v, const Matrix *u_old, const Matrix *v_old,
                               double dx, double dy, double U, double L,
                               double *Ru, double *Rv, double *Rc_mass, double *Rc_div) {
    *Ru = 0.0;
    *Rv = 0.0;
    int nn = u->n * u->n;
    double ru_local = 0.0;
    double rv_local = 0.0;
#pragma omp parallel for reduction(max:ru_local,rv_local) schedule(static)
    for (int k = 0; k < nn; ++k) {
        double du = fabs(u->a[k] - u_old->a[k]);
        double dv = fabs(v->a[k] - v_old->a[k]);
        if (du > ru_local) ru_local = du;
        if (dv > rv_local) rv_local = dv;
    }
    *Ru = ru_local;
    *Rv = rv_local;
    Matrix div = divergence_field(u, v, dx, dy);
    *Rc_div = max_abs_matrix(&div);
    double scale = U * L;
    if (scale < DBL_EPSILON) scale = DBL_EPSILON;
    *Rc_mass = (*Rc_div) * dx * dy / scale;
    matrix_free(&div);
}

