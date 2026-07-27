function T = run_mode_app(mode)
%RUN_MODE_APP Run the MATLAB/Octave solver using a mode aligned with the other solvers.

if nargin < 1
    mode = 'quick';
end
mode = lower(char(mode));

clc; close all;

addpath('src/app');
addpath('src/core');
addpath('src/studies');
addpath('src/validation');
addpath('postprocess');

cfg = default_config(mode);

% On headless clusters, Octave is mainly used to produce CSV/.mat outputs.
% Figure generation can be enabled explicitly with OCTAVE_MAKE_FIGURES=1.
if is_octave_runtime() && ~strcmp(getenv('OCTAVE_MAKE_FIGURES'),'1')
    cfg.make_figures = false;
    cfg.figure_every_case = false;
end

% Data-first cluster runs: keep CSV summaries and residual histories, but avoid figures/field dumps.
if strcmp(getenv('LIDCAVITY_NO_FIGURES'),'1')
    cfg.make_figures = false;
    cfg.figure_every_case = false;
end
if strcmp(getenv('LIDCAVITY_NO_FIELDS'),'1')
    cfg.export_fields = false;
end

if ~exist(cfg.results_dir,'dir'); mkdir(cfg.results_dir); end
if ~exist(cfg.data_dir,'dir'); mkdir(cfg.data_dir); end
if ~exist(cfg.fig_dir,'dir'); mkdir(cfg.fig_dir); end

if is_octave_runtime()
    runtime_name = 'GNU Octave';
else
    runtime_name = 'MATLAB';
end

fprintf('\nLID-DRIVEN CAVITY %s SOLVER\n', runtime_name);
fprintf('Mode: %s\n', mode);
fprintf('Implementations: %s\n', strjoin(cfg.implementations, ', '));

T = run_parametric_study(cfg);

summary_name = sprintf('study_summary_%s_matlab.csv', mode);
if isstruct(T) && isfield(T,'headers') && isfield(T,'rows')
    write_cell_csv(fullfile(cfg.data_dir, summary_name), T.headers, T.rows);
    write_cell_csv(fullfile(cfg.data_dir, 'study_summary.csv'), T.headers, T.rows);
else
    writetable(T, fullfile(cfg.data_dir, summary_name));
    writetable(T, fullfile(cfg.data_dir, 'study_summary.csv'));
end

if cfg.make_figures && ~(isstruct(T) && isfield(T,'rows'))
    plot_study_summary(T, cfg);
end

fprintf('\nFinished %s mode %s. CSV outputs are in %s\n', runtime_name, mode, cfg.data_dir);
end
