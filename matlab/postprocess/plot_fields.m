function plot_fields(result,cfg,case_name)
%PLOT_FIELDS Saves speed contour, pressure contour, streamlines, vorticity.

x = result.x;
y = result.y;
[X,Y] = meshgrid(x,y);

figure('Visible','off');
contourf(X,Y,result.speed,30,'LineColor','none');
colorbar; axis equal tight;
xlabel('x'); ylabel('y');
title('Velocity magnitude');
save_current_figure(fullfile(cfg.fig_dir, case_name + "_speed"));
close;

figure('Visible','off');
contourf(X,Y,result.p,30,'LineColor','none');
colorbar; axis equal tight;
xlabel('x'); ylabel('y');
title('Pressure field');
save_current_figure(fullfile(cfg.fig_dir, case_name + "_pressure"));
close;

figure('Visible','off');
streamslice(X,Y,result.u,result.v);
axis equal tight;
xlabel('x'); ylabel('y');
title('Streamlines');
save_current_figure(fullfile(cfg.fig_dir, case_name + "_streamlines"));
close;

figure('Visible','off');
contourf(X,Y,result.vorticity,30,'LineColor','none');
colorbar; axis equal tight;
xlabel('x'); ylabel('y');
title('Vorticity');
save_current_figure(fullfile(cfg.fig_dir, case_name + "_vorticity"));
close;

figure('Visible','off');
skip = max(1,round(result.N/24));
quiver(X(1:skip:end,1:skip:end),Y(1:skip:end,1:skip:end), ...
       result.u(1:skip:end,1:skip:end),result.v(1:skip:end,1:skip:end));
axis equal tight;
xlabel('x'); ylabel('y');
title('Velocity vectors');
save_current_figure(fullfile(cfg.fig_dir, case_name + "_vectors"));
close;
end
