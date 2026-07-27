function metrics = validate_against_ghia(result)
%VALIDATE_AGAINST_GHIA Compares centerline profiles to Ghia data if available.

data = ghia_data(result.Re);

metrics.available = ~isempty(data);
metrics.u_L2 = NaN;
metrics.v_L2 = NaN;
metrics.u_Linf = NaN;
metrics.v_Linf = NaN;

if isempty(data)
    return;
end

N = result.N;
mid = round((N+1)/2);

% Numerical profiles. u at x=0.5 as function of y, v at y=0.5 as function of x.
u_center = result.u(:,mid);
v_center = result.v(mid,:);

% Interpolate numerical values onto Ghia sample points.
u_num = interp1(result.y, u_center, data.y_u, 'linear', 'extrap');
v_num = interp1(result.x, v_center, data.x_v, 'linear', 'extrap');

eu = u_num(:) - data.u(:);
ev = v_num(:) - data.v(:);

metrics.u_L2 = sqrt(mean(eu.^2));
metrics.v_L2 = sqrt(mean(ev.^2));
metrics.u_Linf = max(abs(eu));
metrics.v_Linf = max(abs(ev));
end
