function [phi, info] = pressure_poisson(rhs,dx,dy,solver_type,cfg)
%PRESSURE_POISSON Solves Laplacian(phi)=rhs with C++-aligned controls.
%
% Supported:
%   'JACOBI'
%   'RBGS'
%   'RBSOR'
%
% The RHS interior mean is removed to satisfy the Neumann compatibility
% condition. This matches the C++ serial solver and makes MATLAB/C++
% comparison cleaner.

N = size(rhs,1);
phi = zeros(N,N);

solver_type = upper(string(solver_type));
den = 2*(dx^2 + dy^2);
C = 2:N-1;
[II,JJ] = ndgrid(C,C);
red = mod(II+JJ,2)==0;
black = ~red;

rhs2 = rhs;
rhs_mean = mean(rhs2(C,C),"all");
rhs2(C,C) = rhs2(C,C) - rhs_mean;

maxIter = cfg.poisson_maxIter;
if isfield(cfg,"poisson_tol_abs")
    tol_abs = cfg.poisson_tol_abs;
else
    tol_abs = 1e-8;
end
if isfield(cfg,"poisson_tol_rel")
    tol_rel = cfg.poisson_tol_rel;
else
    tol_rel = 1e-4;
end
if isfield(cfg,"poisson_check_every")
    check_every = cfg.poisson_check_every;
else
    check_every = 25;
end

if isfield(cfg,"sor_omega") && lower(string(cfg.sor_omega)) == "auto"
    omega = 2/(1 + sin(pi/(N-1)));
    if isfield(cfg,"sor_omega_min")
        omega = max(omega, cfg.sor_omega_min);
    end
    if isfield(cfg,"sor_omega_max")
        omega = min(omega, cfg.sor_omega_max);
    end
else
    omega = cfg.sor_omega;
end

rhs_norm = max(1.0, max(abs(rhs2(C,C)),[],'all'));
res_hist = zeros(maxIter,1);
change_hist = zeros(maxIter,1);
final_res = inf;
final_change = inf;
converged = false;

for it = 1:maxIter

    phi_old = phi;

    if solver_type == "JACOBI"

        phi_new = phi;
        phi_new(C,C) = ((phi(C+1,C)+phi(C-1,C))*dy^2 + ...
                        (phi(C,C+1)+phi(C,C-1))*dx^2 - ...
                        rhs2(C,C)*dx^2*dy^2) / den;
        phi = phi_new;
        phi = apply_pressure_bc(phi);

    elseif solver_type == "RBGS" || solver_type == "RBSOR"

        % Red update
        candidate = ((phi(C+1,C)+phi(C-1,C))*dy^2 + ...
                     (phi(C,C+1)+phi(C,C-1))*dx^2 - ...
                     rhs2(C,C)*dx^2*dy^2) / den;
        block = phi(C,C);

        if solver_type == "RBSOR"
            block(red) = (1-omega)*block(red) + omega*candidate(red);
        else
            block(red) = candidate(red);
        end
        phi(C,C) = block;
        phi = apply_pressure_bc(phi);

        % Black update using updated red neighbors
        candidate = ((phi(C+1,C)+phi(C-1,C))*dy^2 + ...
                     (phi(C,C+1)+phi(C,C-1))*dx^2 - ...
                     rhs2(C,C)*dx^2*dy^2) / den;
        block = phi(C,C);

        if solver_type == "RBSOR"
            block(black) = (1-omega)*block(black) + omega*candidate(black);
        else
            block(black) = candidate(black);
        end
        phi(C,C) = block;
        phi = apply_pressure_bc(phi);

    else
        error("Unknown pressure solver: %s", solver_type);
    end

    final_change = max(abs(phi(:)-phi_old(:)));
    change_hist(it) = final_change;

    if mod(it,check_every)==0 || it==1 || it==maxIter
        final_res = poisson_true_residual(phi,rhs2,dx,dy);
        rel_res = final_res / rhs_norm;
        res_hist(it) = rel_res;
        if final_res < tol_abs || rel_res < tol_rel
            converged = true;
            break;
        end
    end
end

if ~converged
    final_res = poisson_true_residual(phi,rhs2,dx,dy);
end

info.iter = it;
info.converged = converged;
info.omega = omega;
info.final_true_residual = final_res;
info.final_relative_residual = final_res / rhs_norm;
info.final_change = final_change;
info.residual_history = res_hist(1:it);
info.change_history = change_hist(1:it);
end

function res = poisson_true_residual(phi,rhs,dx,dy)
N = size(phi,1);
C = 2:N-1;
lap = (phi(C,C+1) - 2*phi(C,C) + phi(C,C-1))/(dx^2) + ...
      (phi(C+1,C) - 2*phi(C,C) + phi(C-1,C))/(dy^2);
res = max(abs(lap - rhs(C,C)),[],'all');
end
