static GhiaData ghia_data(int Re) {
    GhiaData d;
    d.Re = Re;
    if (Re == 100) {
        d.y_u = {1.0000,0.9766,0.9688,0.9609,0.9531,0.8516,0.7344,0.6172,0.5000,0.4531,0.2813,0.1719,0.1016,0.0703,0.0625,0.0547,0.0000};
        d.u   = {1.0000,0.84123,0.78871,0.73722,0.68717,0.23151,0.00332,-0.13641,-0.20581,-0.21090,-0.15662,-0.10150,-0.06434,-0.04775,-0.04192,-0.03717,0.0000};
        d.x_v = {1.0000,0.9688,0.9609,0.9531,0.9453,0.9063,0.8594,0.8047,0.5000,0.2344,0.2266,0.1563,0.0938,0.0781,0.0703,0.0625,0.0000};
        d.v   = {0.0000,-0.05906,-0.07391,-0.08864,-0.10313,-0.16914,-0.22445,-0.24533,0.05454,0.17527,0.17507,0.16077,0.12317,0.10890,0.10091,0.09233,0.0000};
    } else if (Re == 400) {
        d.y_u = {1.0000,0.9766,0.9688,0.9609,0.9531,0.8516,0.7344,0.6172,0.5000,0.4531,0.2813,0.1719,0.1016,0.0703,0.0625,0.0547,0.0000};
        d.u   = {1.0000,0.75837,0.68439,0.61756,0.55892,0.29093,0.16256,0.02135,-0.11477,-0.17119,-0.32726,-0.24299,-0.14612,-0.10338,-0.09266,-0.08186,0.0000};
        d.x_v = {1.0000,0.9688,0.9609,0.9531,0.9453,0.9063,0.8594,0.8047,0.5000,0.2344,0.2266,0.1563,0.0938,0.0781,0.0703,0.0625,0.0000};
        d.v   = {0.0000,-0.12146,-0.15663,-0.19254,-0.22847,-0.23827,-0.44993,-0.38598,0.05186,0.30174,0.30203,0.28124,0.22965,0.20920,0.19713,0.18360,0.0000};
    } else if (Re == 1000) {
        d.y_u = {1.0000,0.9766,0.9688,0.9609,0.9531,0.8516,0.7344,0.6172,0.5000,0.4531,0.2813,0.1719,0.1016,0.0703,0.0625,0.0547,0.0000};
        d.u   = {1.0000,0.65928,0.57492,0.51117,0.46604,0.33304,0.18719,0.05702,-0.06080,-0.10648,-0.27805,-0.38289,-0.29730,-0.22220,-0.20196,-0.18109,0.0000};
        d.x_v = {1.0000,0.9688,0.9609,0.9531,0.9453,0.9063,0.8594,0.8047,0.5000,0.2344,0.2266,0.1563,0.0938,0.0781,0.0703,0.0625,0.0000};
        d.v   = {0.0000,-0.21388,-0.27669,-0.33714,-0.39188,-0.51550,-0.42665,-0.31966,0.02526,0.32235,0.33075,0.37095,0.32627,0.30353,0.29012,0.27485,0.0000};
    }
    return d;
}

static double interp_linear(const std::vector<double>& x, const std::vector<double>& y, double q) {
    if (x.empty()) return std::numeric_limits<double>::quiet_NaN();
    if (q <= x.front()) return y.front();
    if (q >= x.back()) return y.back();
    const auto it = std::upper_bound(x.begin(), x.end(), q);
    const size_t k = static_cast<size_t>(std::distance(x.begin(), it));
    const double x0 = x[k - 1], x1 = x[k];
    const double y0 = y[k - 1], y1 = y[k];
    const double t = (q - x0) / (x1 - x0);
    return y0 + t * (y1 - y0);
}

static Metrics validate_against_ghia(const Result& result, const Config& cfg) {
    Metrics m;
    GhiaData d = ghia_data(result.Re);
    if (d.y_u.empty()) return m;
    m.available = true;

    const int N = result.N;
    const int mid = static_cast<int>(std::round((N + 1) / 2.0)) - 1; // MATLAB round((N+1)/2)
    std::vector<double> u_center(N), v_center(N);
    for (int i = 0; i < N; ++i) u_center[i] = result.u(i, mid);
    for (int j = 0; j < N; ++j) v_center[j] = result.v(mid, j);

    double sum_u2 = 0.0, sum_v2 = 0.0;
    double linf_u = 0.0, linf_v = 0.0;
    for (size_t k = 0; k < d.y_u.size(); ++k) {
        const double un = interp_linear(result.y, u_center, d.y_u[k]);
        const double e = un - d.u[k];
        sum_u2 += e * e;
        linf_u = std::max(linf_u, std::abs(e));
    }
    for (size_t k = 0; k < d.x_v.size(); ++k) {
        const double vn = interp_linear(result.x, v_center, d.x_v[k]);
        const double e = vn - d.v[k];
        sum_v2 += e * e;
        linf_v = std::max(linf_v, std::abs(e));
    }

    m.u_L2 = std::sqrt(sum_u2 / static_cast<double>(d.y_u.size()));
    m.v_L2 = std::sqrt(sum_v2 / static_cast<double>(d.x_v.size()));
    m.u_Linf = linf_u;
    m.v_Linf = linf_v;

    if (result.Re == 100) {
        m.u_limit = cfg.validation_u_L2_limit_Re100;
        m.v_limit = cfg.validation_v_L2_limit_Re100;
    } else if (result.Re == 400) {
        m.u_limit = cfg.validation_u_L2_limit_Re400;
        m.v_limit = cfg.validation_v_L2_limit_Re400;
    } else if (result.Re == 1000) {
        m.u_limit = cfg.validation_u_L2_limit_Re1000;
        m.v_limit = cfg.validation_v_L2_limit_Re1000;
    } else {
        m.u_limit = std::numeric_limits<double>::infinity();
        m.v_limit = std::numeric_limits<double>::infinity();
    }
    m.pass = (m.u_L2 <= m.u_limit && m.v_L2 <= m.v_limit);
    return m;
}

