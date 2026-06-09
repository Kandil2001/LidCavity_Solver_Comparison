function T = run_mode(mode)
%RUN_MODE Run the MATLAB solver using a mode aligned with the C++ solver.
%
% Example:
%   run_mode('quick')
%   run_mode('full')

if nargin < 1
    mode = "quick";
end
mode = lower(string(mode));

clc; close all;

addpath("core");
addpath("studies");
addpath("validation");
addpath("post");

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
