__global__ void init_fields(double *u, double *v, double *p, int N, double U) {
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    int nn = N * N;
    if (k >= nn) return;
    int i = k / N;
    int j = k - i * N;
    u[k] = 0.0; v[k] = 0.0; p[k] = 0.0;
    if (i == N - 1 && j > 0 && j < N - 1) u[k] = U;
}

__global__ void apply_bc(double *u, double *v, double *p, int N, double U) {
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    if (k >= N) return;
    int j = k;
    u[idx(0,j,N)] = 0.0; u[idx(N-1,j,N)] = (j > 0 && j < N-1) ? U : 0.0;
    v[idx(0,j,N)] = 0.0; v[idx(N-1,j,N)] = 0.0;
    int i = k;
    u[idx(i,0,N)] = 0.0; u[idx(i,N-1,N)] = 0.0;
    v[idx(i,0,N)] = 0.0; v[idx(i,N-1,N)] = 0.0;
    if (p) {
        if (N > 2) {
            p[idx(i,0,N)] = p[idx(i,1,N)];
            p[idx(i,N-1,N)] = p[idx(i,N-2,N)];
            p[idx(0,j,N)] = p[idx(1,j,N)];
            p[idx(N-1,j,N)] = p[idx(N-2,j,N)];
        }
        p[0] = 0.0;
    }
}

__global__ void momentum_kernel(const double *u, const double *v, const double *p,
                                double *us, double *vs, int N, double dx, double dt,
                                double nu, double alpha, int use_upwind) {
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    int nn = N * N;
    if (k >= nn) return;
    int i = k / N;
    int j = k - i * N;
    us[k] = u[k]; vs[k] = v[k];
    if (i <= 0 || i >= N-1 || j <= 0 || j >= N-1) return;

    double uC = u[k], vC = v[k];
    double lap_u = (u[idx(i,j+1,N)] - 2.0*uC + u[idx(i,j-1,N)])/(dx*dx)
                 + (u[idx(i+1,j,N)] - 2.0*uC + u[idx(i-1,j,N)])/(dx*dx);
    double lap_v = (v[idx(i,j+1,N)] - 2.0*vC + v[idx(i,j-1,N)])/(dx*dx)
                 + (v[idx(i+1,j,N)] - 2.0*vC + v[idx(i-1,j,N)])/(dx*dx);
    double du_dx, du_dy, dv_dx, dv_dy;
    if (use_upwind) {
        du_dx = (uC >= 0.0) ? (uC-u[idx(i,j-1,N)])/dx : (u[idx(i,j+1,N)]-uC)/dx;
        dv_dx = (uC >= 0.0) ? (vC-v[idx(i,j-1,N)])/dx : (v[idx(i,j+1,N)]-vC)/dx;
        du_dy = (vC >= 0.0) ? (uC-u[idx(i-1,j,N)])/dx : (u[idx(i+1,j,N)]-uC)/dx;
        dv_dy = (vC >= 0.0) ? (vC-v[idx(i-1,j,N)])/dx : (v[idx(i+1,j,N)]-vC)/dx;
    } else {
        du_dx = (u[idx(i,j+1,N)] - u[idx(i,j-1,N)])/(2.0*dx);
        du_dy = (u[idx(i+1,j,N)] - u[idx(i-1,j,N)])/(2.0*dx);
        dv_dx = (v[idx(i,j+1,N)] - v[idx(i,j-1,N)])/(2.0*dx);
        dv_dy = (v[idx(i+1,j,N)] - v[idx(i-1,j,N)])/(2.0*dx);
    }
    double conv_u = uC*du_dx + vC*du_dy;
    double conv_v = uC*dv_dx + vC*dv_dy;
    double dpdx = (p[idx(i,j+1,N)] - p[idx(i,j-1,N)])/(2.0*dx);
    double dpdy = (p[idx(i+1,j,N)] - p[idx(i-1,j,N)])/(2.0*dx);
    double up = uC + dt*(-conv_u - dpdx + nu*lap_u);
    double vp = vC + dt*(-conv_v - dpdy + nu*lap_v);
    us[k] = (1.0-alpha)*uC + alpha*up;
    vs[k] = (1.0-alpha)*vC + alpha*vp;
}

__global__ void divergence_rhs_kernel(const double *u, const double *v, double *rhs, int N, double dx, double dt) {
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    int nn = N*N;
    if (k >= nn) return;
    int i = k / N, j = k - i*N;
    rhs[k] = 0.0;
    if (i <= 0 || i >= N-1 || j <= 0 || j >= N-1) return;
    double div = (u[idx(i,j+1,N)] - u[idx(i,j-1,N)])/(2.0*dx)
               + (v[idx(i+1,j,N)] - v[idx(i-1,j,N)])/(2.0*dx);
    rhs[k] = div / dt;
}

__global__ void jacobi_kernel(const double *phi, double *phi_new, const double *rhs, int N, double dx) {
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    int nn = N*N;
    if (k >= nn) return;
    int i = k / N, j = k - i*N;
    phi_new[k] = phi[k];
    if (i <= 0 || i >= N-1 || j <= 0 || j >= N-1) return;
    phi_new[k] = 0.25 * (phi[idx(i+1,j,N)] + phi[idx(i-1,j,N)] + phi[idx(i,j+1,N)] + phi[idx(i,j-1,N)] - rhs[k]*dx*dx);
}

__global__ void correct_kernel(double *u, double *v, double *p, const double *us, const double *vs, const double *phi,
                               int N, double dx, double dt, double alpha_p) {
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    int nn = N*N;
    if (k >= nn) return;
    int i = k / N, j = k - i*N;
    u[k] = us[k]; v[k] = vs[k];
    p[k] += alpha_p * phi[k];
    if (i <= 0 || i >= N-1 || j <= 0 || j >= N-1) return;
    double dpdx = (phi[idx(i,j+1,N)] - phi[idx(i,j-1,N)])/(2.0*dx);
    double dpdy = (phi[idx(i+1,j,N)] - phi[idx(i-1,j,N)])/(2.0*dx);
    u[k] = us[k] - dt*dpdx;
    v[k] = vs[k] - dt*dpdy;
}

__global__ void derived_kernel(const double *u, const double *v, const double *p, double *speed, double *vort, int N, double dx) {
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    int nn = N*N;
    if (k >= nn) return;
    int i = k / N, j = k - i*N;
    speed[k] = sqrt(u[k]*u[k] + v[k]*v[k]);
    vort[k] = 0.0;
    if (i > 0 && i < N-1 && j > 0 && j < N-1) {
        vort[k] = (v[idx(i,j+1,N)] - v[idx(i,j-1,N)])/(2.0*dx)
                - (u[idx(i+1,j,N)] - u[idx(i-1,j,N)])/(2.0*dx);
    }
}

