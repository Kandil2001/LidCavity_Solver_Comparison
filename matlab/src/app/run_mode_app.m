function T = run_mode_app(mode)
%RUN_MODE_APP Run the MATLAB solver using a mode aligned with the other solvers.

if nargin < 1
    mode = "quick";
end
mode = lower(string(mode));

clc; close all;

addpath("src/app");
addpath("src/core");
addpath("src/studies");
addpath("src/validation");
addpath("postprocess");

cfg = default_config(mode);

if ~exist(cfg.results_dir,"dir"); mkdir(cfg.results_dir); end
if ~exist(cfg.data_dir,"dir"); mkdir(cfg.data_dir); end
if ~exist(cfg.fig_dir,"dir"); mkdir(cfg.fig_dir); end

fprintf("\nLID-DRIVEN CAVITY MATLAB SOLVER\n");
fprintf("Mode: %s\n", mode);
fprintf("Implementations: %s\n", strjoin(cfg.implementations, ", "));

T = run_parametric_study(cfg);

summary_name = sprintf("study_summary_%s_matlab.csv", mode);
writetable(T, fullfile(cfg.data_dir, summary_name));
writetable(T, fullfile(cfg.data_dir, "study_summary.csv"));

if cfg.make_figures
    plot_study_summary(T, cfg);
end

fprintf("\nFinished MATLAB mode %s. CSV outputs are in %s\n", mode, cfg.data_dir);
end
