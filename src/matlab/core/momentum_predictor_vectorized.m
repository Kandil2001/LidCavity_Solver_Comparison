function [u_star,v_star,dt] = momentum_predictor_vectorized(u,v,p,Re,scheme,cfg)
%MOMENTUM_PREDICTOR_VECTORIZED Full vectorized 2D incompressible NS predictor.
%
% Solves explicit pseudo-transient momentum equations:
%   u* = u + dt[-(u du/dx + v du/dy) - dp/dx + nu Lap(u)]
%   v* = v + dt[-(u dv/dx + v dv/dy) - dp/dy + nu Lap(v)]
%
% Central and sign-based first-order upwind convection are supported.

N = size(u,1);
L = cfg.L;
dx = L/(N-1);
dy = dx;
nu = cfg.U_lid * L / Re;

dt = compute_dt(u,v,dx,dy,nu,cfg);

% Interior slices
C  = 2:N-1;
E  = 3:N;
W  = 1:N-2;
Np = 3:N;
S  = 1:N-2;

uC = u(C,C);  vC = v(C,C);

uE = u(C,E);  uW = u(C,W);  uN = u(Np,C);  uS = u(S,C);
vE = v(C,E);  vW = v(C,W);  vN = v(Np,C);  vS = v(S,C);

pE = p(C,E);  pW = p(C,W);  pN = p(Np,C);  pS = p(S,C);

% Diffusion
lap_u = (uE - 2*uC + uW)/dx^2 + (uN - 2*uC + uS)/dy^2;
lap_v = (vE - 2*vC + vW)/dx^2 + (vN - 2*vC + vS)/dy^2;

scheme = lower(string(scheme));

if scheme == "central"
    du_dx = (uE - uW)/(2*dx);
    du_dy = (uN - uS)/(2*dy);
    dv_dx = (vE - vW)/(2*dx);
    dv_dy = (vN - vS)/(2*dy);

elseif scheme == "upwind"
    % Sign-based donor-cell upwind for each transported variable.
    du_dx = zeros(size(uC));
    du_dy = zeros(size(uC));
    dv_dx = zeros(size(vC));
    dv_dy = zeros(size(vC));

    pos_u = (uC >= 0);
    neg_u = ~pos_u;
    pos_v = (vC >= 0);
    neg_v = ~pos_v;

    du_dx(pos_u) = (uC(pos_u) - uW(pos_u))/dx;
    du_dx(neg_u) = (uE(neg_u) - uC(neg_u))/dx;

    du_dy(pos_v) = (uC(pos_v) - uS(pos_v))/dy;
    du_dy(neg_v) = (uN(neg_v) - uC(neg_v))/dy;

    dv_dx(pos_u) = (vC(pos_u) - vW(pos_u))/dx;
    dv_dx(neg_u) = (vE(neg_u) - vC(neg_u))/dx;

    dv_dy(pos_v) = (vC(pos_v) - vS(pos_v))/dy;
    dv_dy(neg_v) = (vN(neg_v) - vC(neg_v))/dy;

else
    error("Unknown convection scheme: %s", scheme);
end

conv_u = uC .* du_dx + vC .* du_dy;
conv_v = uC .* dv_dx + vC .* dv_dy;

dp_dx = (pE - pW)/(2*dx);
dp_dy = (pN - pS)/(2*dy);

u_pred = uC + dt * (-conv_u - dp_dx + nu*lap_u);
v_pred = vC + dt * (-conv_v - dp_dy + nu*lap_v);

% Under-relaxation of the momentum predictor
u_star = u;
v_star = v;

u_star(C,C) = (1-cfg.alpha_u)*uC + cfg.alpha_u*u_pred;
v_star(C,C) = (1-cfg.alpha_u)*vC + cfg.alpha_u*v_pred;

[u_star,v_star] = apply_lid_bc(u_star,v_star,cfg.U_lid);
end
