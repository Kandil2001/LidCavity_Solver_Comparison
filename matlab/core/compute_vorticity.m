function omega = compute_vorticity(u,v,dx,dy)
%COMPUTE_VORTICITY omega_z = dv/dx - du/dy

N = size(u,1);
omega = zeros(N,N);

omega(2:N-1,2:N-1) = ...
    (v(2:N-1,3:N) - v(2:N-1,1:N-2))/(2*dx) - ...
    (u(3:N,2:N-1) - u(1:N-2,2:N-1))/(2*dy);
end
