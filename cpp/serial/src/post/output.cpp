static std::string quality_label(const Result& result, const Metrics& metrics) {
    if (result.status == "converged" && metrics.available && metrics.pass) return "converged_validated";
    if (result.status == "converged" && metrics.available && !metrics.pass) return "converged_not_validated";
    if (result.status == "converged" && !metrics.available) return "converged_no_benchmark";
    if (result.status != "converged" && metrics.available && metrics.pass) return "validated_but_not_converged";
    return "needs_improvement";
}

static void write_field_csv(const Result& r, const std::string& case_name, const Config& cfg) {
    fs::create_directories(cfg.data_dir);
    const fs::path path = fs::path(cfg.data_dir) / (case_name + "_fields.csv");
    std::ofstream out(path);
    out << std::setprecision(12);
    out << "i,j,x,y,u,v,p,speed,vorticity\n";
    for (int i = 0; i < r.N; ++i) {
        for (int j = 0; j < r.N; ++j) {
            out << i << ',' << j << ',' << r.x[j] << ',' << r.y[i] << ','
                << r.u(i, j) << ',' << r.v(i, j) << ',' << r.p(i, j) << ','
                << r.speed(i, j) << ',' << r.vorticity(i, j) << '\n';
        }
    }
}

static void write_history_csv(const Result& r, const std::string& case_name, const Config& cfg) {
    fs::create_directories(cfg.data_dir);
    const fs::path path = fs::path(cfg.data_dir) / (case_name + "_history.csv");
    std::ofstream out(path);
    out << std::setprecision(12);
    out << "iter,Ru,Rv,Rc_mass,Rc_div,dt,poisson_iters,poisson_relative_residual,poisson_converged\n";
    for (size_t k = 0; k < r.Ru.size(); ++k) {
        out << (k + 1) << ',' << r.Ru[k] << ',' << r.Rv[k] << ',' << r.Rc_mass[k] << ',' << r.Rc_div[k]
            << ',' << r.dt[k] << ',' << r.poisson_iters[k] << ',' << r.poisson_relative_residual[k]
            << ',' << (r.poisson_converged[k] ? 1 : 0) << '\n';
    }
}

static void write_summary_header(std::ofstream& out) {
    out << "CaseID,Implementation,N,Re,Scheme,PressureSolver,Status,Quality,Iterations,LocalMaxIter,"
        << "FinalRu,FinalRv,FinalRcMass,FinalRcDiv,Runtime_s,AvgPoissonIterations,"
        << "AvgPoissonRelResidual,PressureSaturationRatio,HasGhia,ValidationPass,"
        << "Ghia_u_L2,Ghia_v_L2,Ghia_u_Linf,Ghia_v_Linf,Ghia_u_L2_Limit,Ghia_v_L2_Limit\n";
}

static void write_summary_row(std::ofstream& out, int case_id, const Result& r, const Metrics& m, const std::string& quality) {
    out << std::setprecision(12);
    out << case_id << ',' << r.implementation << ',' << r.N << ',' << r.Re << ',' << r.scheme << ',' << r.pressure_solver << ','
        << r.status << ',' << quality << ',' << r.iterations << ',' << r.localMaxIter << ','
        << r.final_Ru << ',' << r.final_Rv << ',' << r.final_Rc_mass << ',' << r.final_Rc_div << ',' << r.runtime << ','
        << r.avg_poisson_iters << ',' << r.avg_poisson_relative_residual << ',' << r.pressure_saturation_ratio << ','
        << (m.available ? 1 : 0) << ',' << (m.pass ? 1 : 0) << ','
        << m.u_L2 << ',' << m.v_L2 << ',' << m.u_Linf << ',' << m.v_Linf << ',' << m.u_limit << ',' << m.v_limit << '\n';
}

