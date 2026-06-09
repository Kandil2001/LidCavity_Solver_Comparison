function dt = compute_dt(u,v,dx,dy,nu,cfg)
%COMPUTE_DT Conservative pseudo-time step for steady pressure correction.

max_vel = max([max(abs(u(:))), max(abs(v(:))), cfg.U_lid, 1e-12]);

dt_conv = cfg.cfl * min(dx,dy) / max_vel;

if nu > 0
    dt_diff = 0.25 * min(dx,dy)^2 / nu;
else
    dt_diff = inf;
end

dt = min([dt_conv, dt_diff, cfg.dt_max]);
end
