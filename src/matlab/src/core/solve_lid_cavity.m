function result = solve_lid_cavity(N,Re,scheme,pressure_solver,implementation,cfg)
%SOLVE_LID_CAVITY 2D incompressible lid-driven cavity pressure correction.
%
% This MATLAB version keeps the original MATLAB algorithmic structure but
% uses the same outer iteration bonuses, relaxation parameters, time-step
% limits, and pressure-solver controls as the C++ serial version.

implementation = lower(char(implementation));
scheme = lower(char(scheme));
pressure_solver = upper(char(pressure_solver));

L = cfg.L;
dx = L/(N-1);
dy = dx;

localMaxIter = cfg.maxIter;
if isfield(cfg,'maxIter_N128_bonus') && N >= 128
    localMaxIter = localMaxIter + cfg.maxIter_N128_bonus;
end
if isfield(cfg,'maxIter_Re1000_bonus') && Re >= 1000
    localMaxIter = localMaxIter + cfg.maxIter_Re1000_bonus;
end
if isfield(cfg,'maxIter_central_bonus') && strcmp(scheme,'central')
    localMaxIter = localMaxIter + cfg.maxIter_central_bonus;
end

u = zeros(N,N);
v = zeros(N,N);
p = zeros(N,N);
[u,v] = apply_lid_bc(u,v,cfg.U_lid);

Ru = zeros(localMaxIter,1);
Rv = zeros(localMaxIter,1);
Rc_mass = zeros(localMaxIter,1);
Rc_div = zeros(localMaxIter,1);
dt_hist = zeros(localMaxIter,1);
poisson_iters = zeros(localMaxIter,1);
poisson_relative_residual = zeros(localMaxIter,1);
poisson_converged = false(localMaxIter,1);

tic_total = tic;
status = 'maxIter';
stagnation_counter = 0;
prev_mass = inf;

for iter = 1:localMaxIter

    u_old = u;
    v_old = v;

    if strcmp(implementation,'vectorized')
        [u_star,v_star,dt] = momentum_predictor_vectorized(u,v,p,Re,scheme,cfg);
    elseif strcmp(implementation,'loop')
        [u_star,v_star,dt] = momentum_predictor_loop(u,v,p,Re,scheme,cfg);
    else
        error('Unknown implementation: %s', implementation);
    end

    if isfield(cfg,'dt_min')
        dt = max(dt, cfg.dt_min);
    end

    % Pressure correction RHS: div(u*) / dt
    div_star = divergence_field(u_star,v_star,dx,dy);
    rhs = div_star / dt;

    [p_prime, pinfo] = pressure_poisson(rhs,dx,dy,pressure_solver,cfg);

    % Velocity correction, vectorized for both implementations.
    u = u_star;
    v = v_star;

    C = 2:N-1;
    dpdx = (p_prime(C,C+1) - p_prime(C,C-1))/(2*dx);
    dpdy = (p_prime(C+1,C) - p_prime(C-1,C))/(2*dy);

    u(C,C) = u_star(C,C) - dt*dpdx;
    v(C,C) = v_star(C,C) - dt*dpdy;

    p = p + cfg.alpha_p*p_prime;
    p = p - mean(p(:)); % remove arbitrary pressure offset

    [u,v] = apply_lid_bc(u,v,cfg.U_lid);

    [Ru(iter),Rv(iter),Rc_mass(iter),Rc_div(iter)] = velocity_residuals(u,v,u_old,v_old,dx,dy,cfg.U_lid,cfg.L);
    dt_hist(iter) = dt;
    poisson_iters(iter) = pinfo.iter;
    if isfield(pinfo,'final_relative_residual')
        poisson_relative_residual(iter) = pinfo.final_relative_residual;
    else
        poisson_relative_residual(iter) = NaN;
    end
    if isfield(pinfo,'converged')
        poisson_converged(iter) = pinfo.converged;
    end

    if any(~isfinite(u(:))) || any(~isfinite(v(:))) || any(~isfinite(p(:))) || ...
       max([Ru(iter),Rv(iter),Rc_div(iter)]) > cfg.diverged_limit
        status = 'diverged';
        break;
    end

    if Rc_mass(iter) > 0.995 * prev_mass
        stagnation_counter = stagnation_counter + 1;
    else
        stagnation_counter = 0;
    end
    prev_mass = Rc_mass(iter);

    if Rc_mass(iter) < cfg.tol_continuity && max(Ru(iter),Rv(iter)) < cfg.tol_velocity
        status = 'converged';
        break;
    end
end

runtime = toc(tic_total);

Ru = Ru(1:iter);
Rv = Rv(1:iter);
Rc_mass = Rc_mass(1:iter);
Rc_div = Rc_div(1:iter);
dt_hist = dt_hist(1:iter);
poisson_iters = poisson_iters(1:iter);
poisson_relative_residual = poisson_relative_residual(1:iter);
poisson_converged = poisson_converged(1:iter);

x = linspace(0,L,N);
y = linspace(0,L,N);
[X,Y] = meshgrid(x,y);

result.N = N;
result.Re = Re;
result.scheme = char(scheme);
result.pressure_solver = char(pressure_solver);
result.implementation = char(implementation);

result.x = x;
result.y = y;
result.X = X;
result.Y = Y;

result.u = u;
result.v = v;
result.p = p;
result.speed = sqrt(u.^2 + v.^2);
result.vorticity = compute_vorticity(u,v,dx,dy);

result.Ru = Ru;
result.Rv = Rv;
result.Rc = Rc_mass;       % kept for old plotting compatibility
result.Rc_mass = Rc_mass;
result.Rc_div = Rc_div;
result.dt = dt_hist;
result.poisson_iters = poisson_iters;
result.poisson_relative_residual = poisson_relative_residual;
result.poisson_converged = poisson_converged;

result.iterations = iter;
result.localMaxIter = localMaxIter;
result.runtime = runtime;
result.status = char(status);
result.final_Ru = Ru(end);
result.final_Rv = Rv(end);
result.final_Rc = Rc_mass(end);      % kept for old table compatibility
result.final_Rc_mass = Rc_mass(end);
result.final_Rc_div = Rc_div(end);
result.avg_poisson_iters = mean(poisson_iters);
valid_p = poisson_relative_residual(isfinite(poisson_relative_residual));
if isempty(valid_p)
    result.avg_poisson_relative_residual = NaN;
else
    result.avg_poisson_relative_residual = mean(valid_p);
end
result.pressure_saturation_ratio = sum(poisson_iters >= cfg.poisson_maxIter) / numel(poisson_iters);
result.stagnation_counter = stagnation_counter;
end
