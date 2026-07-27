function div = divergence_field(u,v,dx,dy)
%DIVERGENCE_FIELD Computes central-difference velocity divergence.

N = size(u,1);
div = zeros(N,N);

div(2:N-1,2:N-1) = ...
    (u(2:N-1,3:N) - u(2:N-1,1:N-2))/(2*dx) + ...
    (v(3:N,2:N-1) - v(1:N-2,2:N-1))/(2*dy);
end
