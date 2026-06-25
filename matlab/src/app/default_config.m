function cfg = default_config(mode)
%DEFAULT_CONFIG Central configuration for the MATLAB lid-driven cavity solver.
%
% This setup is intentionally aligned with the C++ serial solver so that
% MATLAB loop, MATLAB vectorized, and C++ serial results can be compared
% case-by-case using the same numerical controls.
%
% Usage:
%   cfg = default_config();        % quick mode
%   cfg = default_config('quick');
%   cfg = default_config('medium');
%   cfg = default_config('full');
%   cfg = default_config('smoke');

if nargin < 1
    mode = 'quick';
end
mode = lower(char(mode));

cfg.U_lid = 1.0;
cfg.L = 1.0;

% Solver controls aligned with the C++ setup
cfg.maxIter = 4000;
cfg.maxIter_N128_bonus = 3000;
cfg.maxIter_Re1000_bonus = 3000;
cfg.maxIter_central_bonus = 1500;

cfg.tol_continuity = 1e-7;   % scaled continuity/mass residual
cfg.tol_divergence = 2e-3;   % unscaled max(abs(divergence)) used for reporting
cfg.tol_velocity = 5e-7;
cfg.diverged_limit = 1e6;

% Pseudo-time step controls for steady convergence
cfg.cfl = 0.25;
cfg.dt_max = 0.0025;
cfg.dt_min = 1e-6;

% SIMPLE / pressure-correction relaxation
cfg.alpha_u = 0.55;
cfg.alpha_p = 0.20;

% Pressure Poisson controls aligned with the C++ setup
cfg.poisson_maxIter = 2500;
cfg.poisson_tol_abs = 1e-8;
cfg.poisson_tol_rel = 1e-4;
cfg.poisson_check_every = 25;
cfg.sor_omega = 'auto';
cfg.sor_omega_min = 1.15;
cfg.sor_omega_max = 1.90;

% Default full study
cfg.meshes = [32, 64, 128];
cfg.re_list = [100, 400, 1000];
cfg.schemes = {'upwind','central'};
cfg.pressure_solvers = {'RBGS','RBSOR'};
cfg.implementations = {'vectorized','loop'};

% Output
cfg.make_figures = true;
cfg.figure_every_case = true;
cfg.export_csv = true;
cfg.export_fields = true;
cfg.results_dir = 'results';
cfg.data_dir = fullfile('results','data');
cfg.fig_dir = fullfile('results','figures');

% Mode presets matching the C++ executable modes as closely as possible
switch mode
    case 'smoke'
        cfg.meshes = 16;
        cfg.re_list = 100;
        cfg.schemes = {'upwind'};
        cfg.pressure_solvers = {'RBGS'};
        cfg.implementations = {'vectorized','loop'};
        cfg.maxIter = 20;
        cfg.maxIter_N128_bonus = 0;
        cfg.maxIter_Re1000_bonus = 0;
        cfg.maxIter_central_bonus = 0;
        cfg.poisson_maxIter = 50;
        cfg.make_figures = false;
        cfg.figure_every_case = false;

    case 'quick'
        cfg.meshes = [32, 64];
        cfg.re_list = [100, 400];
        cfg.schemes = {'upwind','central'};
        cfg.pressure_solvers = {'RBGS','RBSOR'};
        cfg.implementations = {'vectorized','loop'};
        cfg.maxIter = 2000;
        cfg.maxIter_N128_bonus = 0;
        cfg.maxIter_Re1000_bonus = 0;
        cfg.maxIter_central_bonus = 500;
        cfg.poisson_maxIter = 1200;

    case 'medium'
        cfg.meshes = [32, 64];
        cfg.re_list = [100, 400, 1000];
        cfg.schemes = {'upwind','central'};
        cfg.pressure_solvers = {'RBGS','RBSOR'};
        cfg.implementations = {'vectorized','loop'};
        cfg.maxIter = 3500;
        cfg.maxIter_N128_bonus = 0;
        cfg.poisson_maxIter = 1800;

    case 'full'
        % Keep full defaults above.

    case 'single'
        cfg.meshes = 64;
        cfg.re_list = 100;
        cfg.schemes = {'central'};
        cfg.pressure_solvers = {'RBGS'};
        cfg.implementations = {'vectorized','loop'};

    otherwise
        error('Unknown mode: %s. Use smoke, quick, medium, full, or single.', mode);
end
end
