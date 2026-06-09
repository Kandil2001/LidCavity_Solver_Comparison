struct RunConfig { int N=64, Re=100, maxIter=500, poissonIter=300, blockSize=256; double U=1.0, L=1.0, cfl=0.25, alpha_u=0.55, alpha_p=0.2; bool save_fields=true; std::string scheme="upwind", pressure="JACOBI", mode="quick"; };

static double choose_dt(int N, int Re, const RunConfig& c) {
    double dx = c.L / double(N-1);
    double nu = c.U * c.L / double(Re);
    double dt_conv = c.cfl * dx / c.U;
    double dt_diff = 0.25 * dx * dx / nu;
    double dt = std::min({dt_conv, dt_diff, 0.0025});
    return std::max(dt, 1e-6);
}

