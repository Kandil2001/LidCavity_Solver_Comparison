function [u_star,v_star,dt] = momentum_predictor_loop(u,v,p,Re,scheme,cfg)
%MOMENTUM_PREDICTOR_LOOP Loop reference implementation of the same equations.
% This is intentionally slower but easier to read and verify.

N = size(u,1);
L = cfg.L;
dx = L/(N-1);
dy = dx;
nu = cfg.U_lid * L / Re;

dt = compute_dt(u,v,dx,dy,nu,cfg);

u_star = u;
v_star = v;
scheme = lower(string(scheme));

for i = 2:N-1
    for j = 2:N-1

        uC = u(i,j); vC = v(i,j);

        lap_u = (u(i,j+1)-2*u(i,j)+u(i,j-1))/dx^2 + ...
                (u(i+1,j)-2*u(i,j)+u(i-1,j))/dy^2;

        lap_v = (v(i,j+1)-2*v(i,j)+v(i,j-1))/dx^2 + ...
                (v(i+1,j)-2*v(i,j)+v(i-1,j))/dy^2;

        if scheme == "central"
            du_dx = (u(i,j+1)-u(i,j-1))/(2*dx);
            du_dy = (u(i+1,j)-u(i-1,j))/(2*dy);
            dv_dx = (v(i,j+1)-v(i,j-1))/(2*dx);
            dv_dy = (v(i+1,j)-v(i-1,j))/(2*dy);

        elseif scheme == "upwind"
            if uC >= 0
                du_dx = (u(i,j)-u(i,j-1))/dx;
                dv_dx = (v(i,j)-v(i,j-1))/dx;
            else
                du_dx = (u(i,j+1)-u(i,j))/dx;
                dv_dx = (v(i,j+1)-v(i,j))/dx;
            end

            if vC >= 0
                du_dy = (u(i,j)-u(i-1,j))/dy;
                dv_dy = (v(i,j)-v(i-1,j))/dy;
            else
                du_dy = (u(i+1,j)-u(i,j))/dy;
                dv_dy = (v(i+1,j)-v(i,j))/dy;
            end
        else
            error("Unknown convection scheme: %s", scheme);
        end

        conv_u = uC*du_dx + vC*du_dy;
        conv_v = uC*dv_dx + vC*dv_dy;

        dp_dx = (p(i,j+1)-p(i,j-1))/(2*dx);
        dp_dy = (p(i+1,j)-p(i-1,j))/(2*dy);

        u_pred = u(i,j) + dt*(-conv_u - dp_dx + nu*lap_u);
        v_pred = v(i,j) + dt*(-conv_v - dp_dy + nu*lap_v);

        u_star(i,j) = (1-cfg.alpha_u)*u(i,j) + cfg.alpha_u*u_pred;
        v_star(i,j) = (1-cfg.alpha_u)*v(i,j) + cfg.alpha_u*v_pred;
    end
end

[u_star,v_star] = apply_lid_bc(u_star,v_star,cfg.U_lid);
end
