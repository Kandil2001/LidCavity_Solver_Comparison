/* -------------------------------------------------------------------------
 * Configuration and command-line interface
 * ------------------------------------------------------------------------- */

static void config_defaults(Config *cfg) {
    memset(cfg, 0, sizeof(Config));
    cfg->U_lid = 1.0; cfg->L = 1.0;
    cfg->maxIter = 4000; cfg->maxIter_N128_bonus = 3000; cfg->maxIter_Re1000_bonus = 3000; cfg->maxIter_central_bonus = 1500;
    cfg->tol_mass = 1e-7; cfg->tol_divergence = 2e-3; cfg->tol_velocity = 5e-7; cfg->diverged_limit = 1e6;
    cfg->cfl = 0.25; cfg->dt_max = 0.0025; cfg->dt_min = 1e-6;
    cfg->alpha_u = 0.55; cfg->alpha_p = 0.20;
    cfg->poisson_maxIter = 2500; cfg->poisson_tol_abs = 1e-8; cfg->poisson_tol_rel = 1e-4; cfg->poisson_check_every = 25;
    snprintf(cfg->sor_omega, sizeof(cfg->sor_omega), "auto"); cfg->sor_omega_min = 1.15; cfg->sor_omega_max = 1.90;
    int meshes[] = {32,64,128}; cfg->n_meshes = 3; for (int i=0;i<3;++i) cfg->meshes[i]=meshes[i];
    int re[] = {100,400,1000}; cfg->n_re = 3; for (int i=0;i<3;++i) cfg->re_list[i]=re[i];
    cfg->n_schemes = 2; snprintf(cfg->schemes[0],32,"upwind"); snprintf(cfg->schemes[1],32,"central");
    cfg->n_pressure = 2; snprintf(cfg->pressure_solvers[0],32,"RBGS"); snprintf(cfg->pressure_solvers[1],32,"RBSOR");
    cfg->n_impl = 2; snprintf(cfg->implementations[0],32,"openmp_c_vectorized_style"); snprintf(cfg->implementations[1],32,"openmp_c_looped");
    cfg->validation_u_L2_limit_Re100 = 0.030; cfg->validation_v_L2_limit_Re100 = 0.030;
    cfg->validation_u_L2_limit_Re400 = 0.090; cfg->validation_v_L2_limit_Re400 = 0.120;
    cfg->validation_u_L2_limit_Re1000 = 0.160; cfg->validation_v_L2_limit_Re1000 = 0.180;
    cfg->save_fields = 1;
    snprintf(cfg->results_dir, sizeof(cfg->results_dir), "results");
    snprintf(cfg->data_dir, sizeof(cfg->data_dir), "results/data");
}

static void configure_mode(Config *cfg, const char *mode_in) {
    char mode[32]; strlower_copy(mode, mode_in, sizeof(mode));
    if (strcmp(mode, "quick") == 0) {
        cfg->n_meshes = 2; cfg->meshes[0] = 32; cfg->meshes[1] = 64;
        cfg->n_re = 2; cfg->re_list[0] = 100; cfg->re_list[1] = 400;
        cfg->maxIter = 2000; cfg->maxIter_N128_bonus = 0; cfg->maxIter_Re1000_bonus = 0; cfg->maxIter_central_bonus = 500; cfg->poisson_maxIter = 1200;
    } else if (strcmp(mode, "medium") == 0) {
        cfg->n_meshes = 2; cfg->meshes[0] = 32; cfg->meshes[1] = 64;
        cfg->n_re = 3; cfg->re_list[0] = 100; cfg->re_list[1] = 400; cfg->re_list[2] = 1000;
        cfg->maxIter = 3500; cfg->maxIter_N128_bonus = 0; cfg->poisson_maxIter = 1800;
    } else if (strcmp(mode, "full") == 0) {
        /* defaults */
    } else if (strcmp(mode, "single") == 0) {
        cfg->n_meshes = 1; cfg->meshes[0] = 64;
        cfg->n_re = 1; cfg->re_list[0] = 100;
        cfg->n_schemes = 1; snprintf(cfg->schemes[0],32,"central");
        cfg->n_pressure = 1; snprintf(cfg->pressure_solvers[0],32,"RBGS");
        cfg->n_impl = 2; snprintf(cfg->implementations[0],32,"openmp_c_vectorized_style"); snprintf(cfg->implementations[1],32,"openmp_c_looped");
    } else if (strcmp(mode, "smoke") == 0) {
        cfg->n_meshes = 1; cfg->meshes[0] = 16;
        cfg->n_re = 1; cfg->re_list[0] = 100;
        cfg->n_schemes = 1; snprintf(cfg->schemes[0],32,"upwind");
        cfg->n_pressure = 1; snprintf(cfg->pressure_solvers[0],32,"RBGS");
        cfg->n_impl = 2; snprintf(cfg->implementations[0],32,"openmp_c_vectorized_style"); snprintf(cfg->implementations[1],32,"openmp_c_looped");
        cfg->maxIter = 20; cfg->maxIter_N128_bonus = 0; cfg->maxIter_Re1000_bonus = 0; cfg->maxIter_central_bonus = 0; cfg->poisson_maxIter = 50;
    } else {
        die("Unknown mode (use quick, medium, full, single, or smoke)");
    }
}

static void print_usage(const char *exe) {
    printf("Usage:\n");
    printf("  %s --mode quick|medium|full|single|smoke\n", exe);
    printf("  %s --single --N 64 --Re 100 --scheme central --pressure RBGS --implementation openmp_c_looped\n", exe);
    printf("  %s --single --N 64 --Re 100 --scheme central --pressure RBGS --implementation openmp_c_vectorized_style\n\n", exe);
    printf("Options:\n");
    printf("  --no-fields              Do not write full field CSV files\n");
    printf("  --maxIter VALUE          Override base outer iterations\n");
    printf("  --poisson-maxIter VALUE  Override pressure solver iterations\n");
}

static const char *require_value(int argc, char **argv, int *i, const char *name) {
    if (*i + 1 >= argc) {
        fprintf(stderr, "Missing value for %s\n", name);
        exit(1);
    }
    ++(*i);
    return argv[*i];
}

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    Config cfg; config_defaults(&cfg);
    char mode[32] = "quick";
    int explicit_single = 0;
    int single_N = 64;
    int single_Re = 100;
    char single_scheme[32] = "central";
    char single_pressure[32] = "RBGS";
    char single_impl[32] = "openmp_c_looped";

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) { print_usage(argv[0]); return 0; }
        else if (strcmp(argv[i], "--mode") == 0) { snprintf(mode, sizeof(mode), "%s", require_value(argc, argv, &i, "--mode")); }
        else if (strcmp(argv[i], "--single") == 0) { explicit_single = 1; snprintf(mode, sizeof(mode), "single"); }
        else if (strcmp(argv[i], "--N") == 0) { single_N = atoi(require_value(argc, argv, &i, "--N")); explicit_single = 1; snprintf(mode, sizeof(mode), "single"); }
        else if (strcmp(argv[i], "--Re") == 0) { single_Re = atoi(require_value(argc, argv, &i, "--Re")); explicit_single = 1; snprintf(mode, sizeof(mode), "single"); }
        else if (strcmp(argv[i], "--scheme") == 0) { snprintf(single_scheme, sizeof(single_scheme), "%s", require_value(argc, argv, &i, "--scheme")); explicit_single = 1; snprintf(mode, sizeof(mode), "single"); }
        else if (strcmp(argv[i], "--pressure") == 0) { snprintf(single_pressure, sizeof(single_pressure), "%s", require_value(argc, argv, &i, "--pressure")); explicit_single = 1; snprintf(mode, sizeof(mode), "single"); }
        else if (strcmp(argv[i], "--implementation") == 0) { snprintf(single_impl, sizeof(single_impl), "%s", require_value(argc, argv, &i, "--implementation")); explicit_single = 1; snprintf(mode, sizeof(mode), "single"); }
        else if (strcmp(argv[i], "--no-fields") == 0) { cfg.save_fields = 0; }
        else if (strcmp(argv[i], "--maxIter") == 0) { cfg.maxIter = atoi(require_value(argc, argv, &i, "--maxIter")); }
        else if (strcmp(argv[i], "--poisson-maxIter") == 0) { cfg.poisson_maxIter = atoi(require_value(argc, argv, &i, "--poisson-maxIter")); }
        else { fprintf(stderr, "Unknown argument: %s\n", argv[i]); print_usage(argv[0]); return 1; }
    }

    configure_mode(&cfg, mode);
    if (explicit_single) {
        cfg.n_meshes = 1; cfg.meshes[0] = single_N;
        cfg.n_re = 1; cfg.re_list[0] = single_Re;
        cfg.n_schemes = 1; strlower_copy(cfg.schemes[0], single_scheme, 32);
        cfg.n_pressure = 1; strupper_copy(cfg.pressure_solvers[0], single_pressure, 32);
        cfg.n_impl = 1;
        normalize_c_implementation(cfg.implementations[0], single_impl, 32);
    }

    ensure_dir(cfg.results_dir); ensure_dir(cfg.data_dir);
    char mode_lower[32]; strlower_copy(mode_lower, mode, sizeof(mode_lower));
    char summary_path[1024]; snprintf(summary_path, sizeof(summary_path), "%s/study_summary_%s.csv", cfg.data_dir, mode_lower);
    FILE *summary = fopen(summary_path, "w");
    if (!summary) die("Could not open summary CSV");
    write_summary_header(summary);

    int nCases = cfg.n_meshes * cfg.n_re * cfg.n_schemes * cfg.n_pressure * cfg.n_impl;
    printf("\nLID-DRIVEN CAVITY C OPENMP SOLVER\n");
    printf("Mode: %s\n", mode);
    printf("Total simulations: %d\n", nCases);
    printf("Summary: %s\n\n", summary_path);

    int case_id = 0;
    for (int iN = 0; iN < cfg.n_meshes; ++iN) {
        int N = cfg.meshes[iN];
        for (int iR = 0; iR < cfg.n_re; ++iR) {
            int Re = cfg.re_list[iR];
            for (int is = 0; is < cfg.n_schemes; ++is) {
                for (int ip = 0; ip < cfg.n_pressure; ++ip) {
                    for (int ii = 0; ii < cfg.n_impl; ++ii) {
                        ++case_id;
                        char scheme_l[32]; strlower_copy(scheme_l, cfg.schemes[is], 32);
                        char press_u[32]; strupper_copy(press_u, cfg.pressure_solvers[ip], 32);
                        char impl_l[32]; strlower_copy(impl_l, cfg.implementations[ii], 32);
                        char case_name[256];
                        snprintf(case_name, sizeof(case_name), "case_%03d_N%d_Re%d_%s_%s_%s", case_id, N, Re, scheme_l, press_u, impl_l);
                        printf("[%03d] N=%d Re=%d Scheme=%s Pressure=%s Implementation=%s\n", case_id, N, Re, scheme_l, press_u, impl_l);
                        Result r = solve_lid_cavity(N, Re, scheme_l, press_u, impl_l, &cfg);
                        Metrics m = validate_against_ghia(&r, &cfg);
                        const char *quality = quality_label(&r, &m);
                        write_summary_row(summary, case_id, &r, &m, quality);
                        fflush(summary);
                        write_history_csv(&r, case_name, &cfg);
                        if (cfg.save_fields) write_field_csv(&r, case_name, &cfg);
                        printf("      status=%s quality=%s iter=%d/%d Rc_mass=%.3e Rc_div=%.3e runtime=%.2fs avgPiter=%.1f pSat=%.2f\n",
                               r.status, quality, r.iterations, r.localMaxIter, r.final_Rc_mass, r.final_Rc_div, r.runtime, r.avg_poisson_iters, r.pressure_saturation_ratio);
                        if (m.available) {
                            printf("      Ghia L2: u=%.3e(limit %.3e), v=%.3e(limit %.3e), pass=%d\n", m.u_L2, m.u_limit, m.v_L2, m.v_limit, m.pass);
                        }
                        free_result(&r);
                    }
                }
            }
        }
    }
    fclose(summary);
    printf("\nFinished. CSV outputs are in %s\n", cfg.data_dir);
    return 0;
}
