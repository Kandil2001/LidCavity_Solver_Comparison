function result = run_single_case()
%RUN_SINGLE_CASE Fast test case for debugging.

addpath("core");
addpath("validation");
addpath("post");

cfg = default_config();
cfg.maxIter = 500;
cfg.make_figures = true;

N = 32;
Re = 100;
scheme = 'upwind';
pressure_solver = 'RBSOR';
implementation = 'vectorized';

result = solve_lid_cavity(N,Re,scheme,pressure_solver,implementation,cfg);

case_name = sprintf("single_N%d_Re%d_%s_%s_%s",N,Re,scheme,pressure_solver,implementation);
plot_residuals(result,cfg,case_name);
plot_fields(result,cfg,case_name);
plot_validation(result,cfg,case_name);

disp(result);
end
