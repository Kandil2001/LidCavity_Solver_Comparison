/* -------------------------------------------------------------------------
 * Validation and CSV export
 * ------------------------------------------------------------------------- */

static int ghia_data(int Re, const double **yu, const double **gu, const double **xv, const double **gv, int *n) {
    static const double yu100[] = {1.0000,0.9766,0.9688,0.9609,0.9531,0.8516,0.7344,0.6172,0.5000,0.4531,0.2813,0.1719,0.1016,0.0703,0.0625,0.0547,0.0000};
    static const double u100[]  = {1.0000,0.84123,0.78871,0.73722,0.68717,0.23151,0.00332,-0.13641,-0.20581,-0.21090,-0.15662,-0.10150,-0.06434,-0.04775,-0.04192,-0.03717,0.0000};
    static const double xv100[] = {1.0000,0.9688,0.9609,0.9531,0.9453,0.9063,0.8594,0.8047,0.5000,0.2344,0.2266,0.1563,0.0938,0.0781,0.0703,0.0625,0.0000};
    static const double v100[]  = {0.0000,-0.05906,-0.07391,-0.08864,-0.10313,-0.16914,-0.22445,-0.24533,0.05454,0.17527,0.17507,0.16077,0.12317,0.10890,0.10091,0.09233,0.0000};
    static const double u400[]  = {1.0000,0.75837,0.68439,0.61756,0.55892,0.29093,0.16256,0.02135,-0.11477,-0.17119,-0.32726,-0.24299,-0.14612,-0.10338,-0.09266,-0.08186,0.0000};
    static const double v400[]  = {0.0000,-0.12146,-0.15663,-0.19254,-0.22847,-0.23827,-0.44993,-0.38598,0.05186,0.30174,0.30203,0.28124,0.22965,0.20920,0.19713,0.18360,0.0000};
    static const double u1000[] = {1.0000,0.65928,0.57492,0.51117,0.46604,0.33304,0.18719,0.05702,-0.06080,-0.10648,-0.27805,-0.38289,-0.29730,-0.22220,-0.20196,-0.18109,0.0000};
    static const double v1000[] = {0.0000,-0.21388,-0.27669,-0.33714,-0.39188,-0.51550,-0.42665,-0.31966,0.02526,0.32235,0.33075,0.37095,0.32627,0.30353,0.29012,0.27485,0.0000};
    *n = 17;
    *yu = yu100; *xv = xv100;
    if (Re == 100) { *gu = u100; *gv = v100; return 1; }
    if (Re == 400) { *gu = u400; *gv = v400; return 1; }
    if (Re == 1000) { *gu = u1000; *gv = v1000; return 1; }
    return 0;
}

static double interp_linear(const double *x, const double *y, int n, double q) {
    if (n <= 0) return NAN;
    if (q <= x[0]) return y[0];
    if (q >= x[n - 1]) return y[n - 1];
    int k = 1;
    while (k < n && x[k] < q) ++k;
    double x0 = x[k - 1], x1 = x[k];
    double y0 = y[k - 1], y1 = y[k];
    double t = (q - x0) / (x1 - x0);
    return y0 + t * (y1 - y0);
}

static Metrics validate_against_ghia(const Result *r, const Config *cfg) {
    Metrics m;
    m.available = 0; m.pass = 0;
    m.u_L2 = m.v_L2 = m.u_Linf = m.v_Linf = m.u_limit = m.v_limit = NAN;
    const double *yu, *gu, *xv, *gv;
    int n;
    if (!ghia_data(r->Re, &yu, &gu, &xv, &gv, &n)) return m;
    m.available = 1;
    int N = r->N;
    int mid = (int)floor((N + 1) / 2.0 + 0.5) - 1;
    double *u_center = (double*)malloc((size_t)N * sizeof(double));
    double *v_center = (double*)malloc((size_t)N * sizeof(double));
    if (!u_center || !v_center) die("Out of memory");
    for (int i = 0; i < N; ++i) u_center[i] = AT(r->u, i, mid);
    for (int j = 0; j < N; ++j) v_center[j] = AT(r->v, mid, j);
    double sum_u2 = 0.0, sum_v2 = 0.0, linf_u = 0.0, linf_v = 0.0;
    for (int k = 0; k < n; ++k) {
        double un = interp_linear(r->y, u_center, N, yu[k]);
        double e = un - gu[k];
        sum_u2 += e * e;
        if (fabs(e) > linf_u) linf_u = fabs(e);
    }
    for (int k = 0; k < n; ++k) {
        double vn = interp_linear(r->x, v_center, N, xv[k]);
        double e = vn - gv[k];
        sum_v2 += e * e;
        if (fabs(e) > linf_v) linf_v = fabs(e);
    }
    free(u_center); free(v_center);
    m.u_L2 = sqrt(sum_u2 / (double)n);
    m.v_L2 = sqrt(sum_v2 / (double)n);
    m.u_Linf = linf_u;
    m.v_Linf = linf_v;
    if (r->Re == 100) { m.u_limit = cfg->validation_u_L2_limit_Re100; m.v_limit = cfg->validation_v_L2_limit_Re100; }
    else if (r->Re == 400) { m.u_limit = cfg->validation_u_L2_limit_Re400; m.v_limit = cfg->validation_v_L2_limit_Re400; }
    else if (r->Re == 1000) { m.u_limit = cfg->validation_u_L2_limit_Re1000; m.v_limit = cfg->validation_v_L2_limit_Re1000; }
    else { m.u_limit = INFINITY; m.v_limit = INFINITY; }
    m.pass = (m.u_L2 <= m.u_limit && m.v_L2 <= m.v_limit);
    return m;
}

static const char *quality_label(const Result *r, const Metrics *m) {
    if (strcmp(r->status, "converged") == 0 && m->available && m->pass) return "converged_validated";
    if (strcmp(r->status, "converged") == 0 && m->available && !m->pass) return "converged_not_validated";
    if (strcmp(r->status, "converged") == 0 && !m->available) return "converged_no_benchmark";
    if (strcmp(r->status, "converged") != 0 && m->available && m->pass) return "validated_but_not_converged";
    return "needs_improvement";
}

static void write_field_csv(const Result *r, const char *case_name, const Config *cfg) {
    ensure_dir(cfg->results_dir); ensure_dir(cfg->data_dir);
    char path[1024]; snprintf(path, sizeof(path), "%s/%s_fields.csv", cfg->data_dir, case_name);
    FILE *f = fopen(path, "w");
    if (!f) die("Could not open field CSV");
    fprintf(f, "i,j,x,y,u,v,p,speed,vorticity\n");
    for (int i = 0; i < r->N; ++i) {
        for (int j = 0; j < r->N; ++j) {
            fprintf(f, "%d,%d,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g\n",
                    i, j, r->x[j], r->y[i], AT(r->u, i, j), AT(r->v, i, j), AT(r->p, i, j), AT(r->speed, i, j), AT(r->vorticity, i, j));
        }
    }
    fclose(f);
}

static void write_history_csv(const Result *r, const char *case_name, const Config *cfg) {
    ensure_dir(cfg->results_dir); ensure_dir(cfg->data_dir);
    char path[1024]; snprintf(path, sizeof(path), "%s/%s_history.csv", cfg->data_dir, case_name);
    FILE *f = fopen(path, "w");
    if (!f) die("Could not open history CSV");
    fprintf(f, "iter,Ru,Rv,Rc_mass,Rc_div,dt,poisson_iters,poisson_relative_residual,poisson_converged\n");
    for (int k = 0; k < r->hist_count; ++k) {
        fprintf(f, "%d,%.12g,%.12g,%.12g,%.12g,%.12g,%d,%.12g,%d\n",
                k + 1, r->Ru[k], r->Rv[k], r->Rc_mass[k], r->Rc_div[k], r->dt[k], r->poisson_iters[k],
                r->poisson_relative_residual[k], r->poisson_converged[k]);
    }
    fclose(f);
}

static void write_summary_header(FILE *f) {
    fprintf(f, "CaseID,Implementation,N,Re,Scheme,PressureSolver,Status,Quality,Iterations,LocalMaxIter,");
    fprintf(f, "FinalRu,FinalRv,FinalRcMass,FinalRcDiv,Runtime_s,AvgPoissonIterations,");
    fprintf(f, "AvgPoissonRelResidual,PressureSaturationRatio,HasGhia,ValidationPass,");
    fprintf(f, "Ghia_u_L2,Ghia_v_L2,Ghia_u_Linf,Ghia_v_Linf,Ghia_u_L2_Limit,Ghia_v_L2_Limit\n");
}

static void write_summary_row(FILE *f, int case_id, const Result *r, const Metrics *m, const char *quality) {
    fprintf(f, "%d,%s,%d,%d,%s,%s,%s,%s,%d,%d,", case_id, r->implementation, r->N, r->Re, r->scheme, r->pressure_solver, r->status, quality, r->iterations, r->localMaxIter);
    fprintf(f, "%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,", r->final_Ru, r->final_Rv, r->final_Rc_mass, r->final_Rc_div, r->runtime, r->avg_poisson_iters);
    fprintf(f, "%.12g,%.12g,%d,%d,", r->avg_poisson_relative_residual, r->pressure_saturation_ratio, m->available, m->pass);
    fprintf(f, "%.12g,%.12g,%.12g,%.12g,%.12g,%.12g\n", m->u_L2, m->v_L2, m->u_Linf, m->v_Linf, m->u_limit, m->v_limit);
}

