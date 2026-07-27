function [Ru,Rv,Rc_mass,Rc_div] = velocity_residuals(u,v,u_old,v_old,dx,dy,U,L)
%VELOCITY_RESIDUALS Reports velocity changes and continuity residuals.
%
% Rc_div  = max(abs(divergence))
% Rc_mass = scaled continuity residual, aligned with the C++ output.

if nargin < 7
    U = 1.0;
end
if nargin < 8
    L = 1.0;
end

Ru = max(abs(u(:)-u_old(:)));
Rv = max(abs(v(:)-v_old(:)));

div = divergence_field(u,v,dx,dy);
Rc_div = max(abs(div(:)));
scale = max(U*L, eps);
Rc_mass = Rc_div * dx * dy / scale;
end
