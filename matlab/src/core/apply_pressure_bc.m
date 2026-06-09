function p = apply_pressure_bc(p)
%APPLY_PRESSURE_BC Homogeneous Neumann pressure-correction BC + reference.
%
% dp/dn = 0 at all cavity walls.
% One reference value removes the arbitrary pressure constant.

p(:,1)   = p(:,2);
p(:,end) = p(:,end-1);
p(1,:)   = p(2,:);
p(end,:) = p(end-1,:);

p(1,1) = 0.0;
end
