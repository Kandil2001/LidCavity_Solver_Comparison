static void write_outputs(const RunConfig& cfg, double runtime, const std::vector<double>& u, const std::vector<double>& v, const std::vector<double>& p, const std::vector<double>& speed, const std::vector<double>& vort) {
    fs::create_directories("results/data");
    std::ofstream sum("results/data/study_summary_cuda.csv");
    sum << "CaseID,Implementation,N,Re,Scheme,PressureSolver,Status,Quality,Iterations,LocalMaxIter,FinalRu,FinalRv,FinalRcMass,FinalRcDiv,Runtime_s,AvgPoissonIterations,AvgPoissonRelResidual,PressureSaturationRatio,HasGhia,ValidationPass,Ghia_u_L2,Ghia_v_L2,Ghia_u_Linf,Ghia_v_Linf,Ghia_u_L2_Limit,Ghia_v_L2_Limit\n";
    sum << "1,cuda_projection_jacobi," << cfg.N << ',' << cfg.Re << ',' << cfg.scheme << ",JACOBI,maxIter,gpu_benchmark," << cfg.maxIter << ',' << cfg.maxIter << ",nan,nan,nan,nan," << std::setprecision(12) << runtime << ',' << cfg.poissonIter << ",nan,0,0,0,nan,nan,nan,nan,nan,nan\n";
    sum.close();

    if (!cfg.save_fields) return;
    std::ofstream f("results/data/case_001_N" + std::to_string(cfg.N) + "_Re" + std::to_string(cfg.Re) + "_" + cfg.scheme + "_JACOBI_cuda_projection_jacobi_fields.csv");
    f << "i,j,x,y,u,v,p,speed,vorticity\n";
    double dx = cfg.L / double(cfg.N-1);
    for (int i=0;i<cfg.N;++i) for (int j=0;j<cfg.N;++j) {
        int k = idx(i,j,cfg.N);
        f << i << ',' << j << ',' << j*dx << ',' << i*dx << ',' << std::setprecision(12) << u[k] << ',' << v[k] << ',' << p[k] << ',' << speed[k] << ',' << vort[k] << '\n';
    }
}

