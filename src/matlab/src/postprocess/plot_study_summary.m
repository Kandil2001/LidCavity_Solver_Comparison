function plot_study_summary(T,cfg)
%PLOT_STUDY_SUMMARY Generates study-level plots from the summary table.

if isempty(T)
    return;
end

figure('Visible','off');
cats = categorical(T.Implementation);
boxchart(cats,T.Runtime_s);
grid on;
ylabel('Runtime [s]');
title('Runtime: loop vs vectorized');
save_current_figure(fullfile(cfg.fig_dir, "study_runtime_implementation"));
close;

figure('Visible','off');
cats = categorical(T.PressureSolver);
boxchart(cats,T.AvgPoissonIterations);
grid on;
ylabel('Average pressure iterations');
title('Pressure solver comparison');
save_current_figure(fullfile(cfg.fig_dir, "study_pressure_solver_iterations"));
close;

valid = ~isnan(T.Ghia_u_L2);
if any(valid)
    figure('Visible','off');
    gscatter(T.N(valid), T.Ghia_u_L2(valid), string(T.Scheme(valid)));
    grid on;
    xlabel('Mesh size N');
    ylabel('L2 error in u centerline');
    title('Mesh / scheme validation error vs Ghia');
    save_current_figure(fullfile(cfg.fig_dir, "study_ghia_error"));
    close;
end
end
