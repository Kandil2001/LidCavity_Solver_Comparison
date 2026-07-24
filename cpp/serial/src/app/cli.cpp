static void configure_paper_protocol(Config& cfg) {
    cfg.paper_protocol = true;
    cfg.use_divergence_convergence = true;
    cfg.require_pressure_convergence = true;

    cfg.maxIter = 50000;
    cfg.maxIter_N128_bonus = 0;
    cfg.maxIter_Re1000_bonus = 0;
    cfg.maxIter_central_bonus = 0;

    cfg.tol_velocity = 1e-8;
    cfg.tol_divergence = 1e-6;
    cfg.poisson_tol_abs = 1e-10;
    cfg.poisson_tol_rel = 1e-8;
    cfg.poisson_check_every = 10;
    cfg.poisson_maxIter = 5000;
}

static void configure_mode(Config& cfg, const std::string& mode) {
    const std::string m = lower(mode);
    if (m == "quick") {
        cfg.meshes = {32, 64};
        cfg.re_list = {100, 400};
        cfg.maxIter = 2000;
        cfg.maxIter_N128_bonus = 0;
        cfg.maxIter_Re1000_bonus = 0;
        cfg.maxIter_central_bonus = 500;
        cfg.poisson_maxIter = 1200;
    } else if (m == "medium") {
        cfg.meshes = {32, 64};
        cfg.re_list = {100, 400, 1000};
        cfg.maxIter = 3500;
        cfg.maxIter_N128_bonus = 0;
        cfg.poisson_maxIter = 1800;
    } else if (m == "full") {
        // Defaults, equivalent to the current full repository study.
    } else if (m == "paper") {
        cfg.meshes = {33, 65, 129, 257};
        cfg.re_list = {100, 400, 1000};
        cfg.schemes = {"central"};
        cfg.pressure_solvers = {"RBSOR"};
        cfg.implementations = {"serial_cpp"};
        configure_paper_protocol(cfg);
    } else if (m == "single") {
        cfg.meshes = {64};
        cfg.re_list = {100};
        cfg.schemes = {"central"};
        cfg.pressure_solvers = {"RBGS"};
        cfg.implementations = {"serial_cpp"};
    } else if (m == "smoke") {
        cfg.meshes = {16};
        cfg.re_list = {100};
        cfg.schemes = {"upwind"};
        cfg.pressure_solvers = {"RBGS"};
        cfg.implementations = {"serial_cpp"};
        cfg.maxIter = 20;
        cfg.maxIter_N128_bonus = 0;
        cfg.maxIter_Re1000_bonus = 0;
        cfg.maxIter_central_bonus = 0;
        cfg.poisson_maxIter = 50;
    } else {
        throw std::runtime_error("Unknown mode: " + mode + " (use quick, medium, full, paper, single, or smoke)");
    }
}

static void print_usage(const char* exe) {
    std::cout << "Usage:\n"
              << "  " << exe << " --mode quick|medium|full|paper|single|smoke\n"
              << "  " << exe << " --single --N 65 --Re 100 --scheme central --pressure RBSOR --paper-protocol\n\n"
              << "Options:\n"
              << "  --paper-protocol         Apply the draft paper convergence protocol to a selected case\n"
              << "  --no-fields              Do not write full field CSV files\n"
              << "  --maxIter VALUE          Override base outer iterations after mode configuration\n"
              << "  --poisson-maxIter VALUE  Override pressure solver iterations after mode configuration\n"
              << "\nImplementation note: this C++ package has one serial_cpp solver. MATLAB labels loop/vectorized are accepted as aliases only.\n";
}

int main(int argc, char** argv) {
    std::cout << std::unitbuf;
    std::cerr << std::unitbuf;
    Config cfg;
    std::string mode = "quick";
    bool explicit_single = false;
    bool paper_protocol_requested = false;
    int single_N = 64;
    int single_Re = 100;
    std::string single_scheme = "central";
    std::string single_pressure = "RBGS";
    std::string single_implementation = "serial_cpp";
    int max_iter_override = -1;
    int poisson_max_iter_override = -1;

    try {
        for (int i = 1; i < argc; ++i) {
            std::string arg = argv[i];
            auto require_value = [&](const std::string& name) -> std::string {
                if (i + 1 >= argc) throw std::runtime_error("Missing value for " + name);
                return argv[++i];
            };

            if (arg == "--help" || arg == "-h") {
                print_usage(argv[0]);
                return 0;
            } else if (arg == "--mode") {
                mode = require_value(arg);
            } else if (arg == "--single") {
                explicit_single = true;
                mode = "single";
            } else if (arg == "--N") {
                single_N = std::stoi(require_value(arg));
                explicit_single = true;
                mode = "single";
            } else if (arg == "--Re") {
                single_Re = std::stoi(require_value(arg));
                explicit_single = true;
                mode = "single";
            } else if (arg == "--scheme") {
                single_scheme = require_value(arg);
                explicit_single = true;
                mode = "single";
            } else if (arg == "--pressure") {
                single_pressure = require_value(arg);
                explicit_single = true;
                mode = "single";
            } else if (arg == "--implementation") {
                single_implementation = require_value(arg);
                explicit_single = true;
                mode = "single";
            } else if (arg == "--paper-protocol") {
                paper_protocol_requested = true;
            } else if (arg == "--no-fields") {
                cfg.save_fields = false;
            } else if (arg == "--maxIter") {
                max_iter_override = std::stoi(require_value(arg));
            } else if (arg == "--poisson-maxIter") {
                poisson_max_iter_override = std::stoi(require_value(arg));
            } else {
                throw std::runtime_error("Unknown argument: " + arg);
            }
        }

        configure_mode(cfg, mode);
        if (paper_protocol_requested && lower(mode) != "paper") {
            configure_paper_protocol(cfg);
        }
        if (max_iter_override > 0) cfg.maxIter = max_iter_override;
        if (poisson_max_iter_override > 0) cfg.poisson_maxIter = poisson_max_iter_override;

        if (explicit_single) {
            cfg.meshes = {single_N};
            cfg.re_list = {single_Re};
            cfg.schemes = {lower(single_scheme)};
            cfg.pressure_solvers = {upper(single_pressure)};
            cfg.implementations = {normalize_implementation(single_implementation)};
        }

        fs::create_directories(cfg.data_dir);
        std::string summary_label = lower(mode);
        if (cfg.paper_protocol && lower(mode) == "single") summary_label = "paper_single";
        const fs::path summary_path = fs::path(cfg.data_dir) / ("study_summary_" + summary_label + ".csv");
        std::ofstream summary(summary_path);
        write_summary_header(summary);

        const int nCases = static_cast<int>(cfg.meshes.size() * cfg.re_list.size() * cfg.schemes.size()
                         * cfg.pressure_solvers.size() * cfg.implementations.size());
        std::cout << "\nLID-DRIVEN CAVITY C++ SOLVER\n";
        std::cout << "Mode: " << mode << "\n";
        std::cout << "Paper protocol: " << (cfg.paper_protocol ? "enabled" : "disabled") << "\n";
        std::cout << "Total simulations: " << nCases << "\n";
        std::cout << "Summary: " << summary_path.string() << "\n\n";

        int case_id = 0;
        for (int N : cfg.meshes) {
            for (int Re : cfg.re_list) {
                for (const auto& scheme : cfg.schemes) {
                    for (const auto& pressure_solver : cfg.pressure_solvers) {
                        for (const auto& implementation : cfg.implementations) {
                            ++case_id;
                            std::ostringstream name;
                            name << "case_" << std::setw(3) << std::setfill('0') << case_id << std::setfill(' ')
                                 << "_N" << N << "_Re" << Re << "_" << lower(scheme)
                                 << "_" << upper(pressure_solver) << "_" << lower(implementation);
                            const std::string case_name = name.str();

                            std::cout << "[" << std::setw(3) << std::setfill('0') << case_id << std::setfill(' ')
                                      << "] N=" << N << " Re=" << Re << " Scheme=" << scheme
                                      << " Pressure=" << pressure_solver << " Implementation=" << implementation << "\n";

                            Result r = solve_lid_cavity(N, Re, scheme, pressure_solver, implementation, cfg);
                            Metrics metrics = validate_against_ghia(r, cfg);
                            const std::string quality = quality_label(r, metrics);
                            write_summary_row(summary, case_id, r, metrics, quality, cfg);
                            summary.flush();
                            write_history_csv(r, case_name, cfg);
                            if (cfg.save_fields) write_field_csv(r, case_name, cfg);

                            std::cout << "      status=" << r.status << " quality=" << quality
                                      << " iter=" << r.iterations << "/" << r.localMaxIter
                                      << " dU=" << std::scientific << std::setprecision(3) << std::max(r.final_Ru, r.final_Rv)
                                      << " div=" << r.final_Rc_div
                                      << " pRel=" << r.final_poisson_relative_residual
                                      << " pConv=" << (r.final_pressure_converged ? 1 : 0)
                                      << " runtime=" << std::fixed << std::setprecision(2) << r.runtime << "s"
                                      << " avgPiter=" << std::setprecision(1) << r.avg_poisson_iters
                                      << " pSat=" << std::setprecision(2) << r.pressure_saturation_ratio << "\n";
                            if (metrics.available) {
                                std::cout << "      Ghia L2: u=" << std::scientific << std::setprecision(3) << metrics.u_L2
                                          << "(limit " << metrics.u_limit << "), v=" << metrics.v_L2
                                          << "(limit " << metrics.v_limit << "), pass=" << (metrics.pass ? 1 : 0) << "\n";
                            }
                            std::cout << std::defaultfloat;
                        }
                    }
                }
            }
        }

        std::cout << "\nFinished. CSV outputs are in " << cfg.data_dir << "\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << "\n";
        print_usage(argv[0]);
        return 1;
    }
}
