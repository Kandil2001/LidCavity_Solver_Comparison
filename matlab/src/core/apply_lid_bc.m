function [u,v] = apply_lid_bc(u,v,U_lid)
%APPLY_LID_BC Applies lid-driven cavity no-slip boundary conditions.
%
% Grid convention:
%   rows    -> y direction
%   columns -> x direction
%   row 1   -> bottom wall
%   row end -> moving lid

u(1,:)   = 0.0;       % bottom
u(end,:) = U_lid;     % top moving lid
u(:,1)   = 0.0;       % left
u(:,end) = 0.0;       % right

v(1,:)   = 0.0;
v(end,:) = 0.0;
v(:,1)   = 0.0;
v(:,end) = 0.0;
end
