function plot_validation(result,cfg,case_name)
%PLOT_VALIDATION Centerline comparison against Ghia data when available.

data = ghia_data(result.Re);
if isempty(data)
    return;
end

mid = round((result.N+1)/2);

figure('Visible','off');
plot(result.u(:,mid), result.y, 'LineWidth', 1.5); hold on;
plot(data.u, data.y_u, 'o', 'LineWidth', 1.2);
grid on;
xlabel('u velocity at x=0.5');
ylabel('y');
legend('Solver','Ghia et al.','Location','best');
title(sprintf('Vertical centerline validation, Re=%d', result.Re));
save_current_figure(fullfile(cfg.fig_dir, case_name + "_ghia_u"));
close;

figure('Visible','off');
plot(result.x, result.v(mid,:), 'LineWidth', 1.5); hold on;
plot(data.x_v, data.v, 'o', 'LineWidth', 1.2);
grid on;
xlabel('x');
ylabel('v velocity at y=0.5');
legend('Solver','Ghia et al.','Location','best');
title(sprintf('Horizontal centerline validation, Re=%d', result.Re));
save_current_figure(fullfile(cfg.fig_dir, case_name + "_ghia_v"));
close;
end
