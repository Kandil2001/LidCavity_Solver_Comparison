function plot_residuals(result,cfg,case_name)
%PLOT_RESIDUALS Saves residual history.

figure('Visible','off');
semilogy(result.Ru,'LineWidth',1.5); hold on;
semilogy(result.Rv,'LineWidth',1.5);
semilogy(result.Rc,'LineWidth',1.5);
grid on;
xlabel('Outer iteration');
ylabel('Residual');
legend('R_u','R_v','R_c','Location','best');
title(sprintf('Residuals: N=%d Re=%d %s %s %s', ...
    result.N,result.Re,result.scheme,result.pressure_solver,result.implementation), ...
    'Interpreter','none');

save_current_figure(fullfile(cfg.fig_dir, case_name + "_residuals"));
close;
end
