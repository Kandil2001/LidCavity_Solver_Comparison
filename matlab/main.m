% MAIN ENTRY POINT
% Same-setup MATLAB lid-driven cavity study.
%
% Run from MATLAB:
%   main                 % quick mode
%   run_quick
%   run_medium
%   run_full

clear; clc; close all;

addpath("core");
addpath("studies");
addpath("validation");
addpath("post");

cfg = default_config("quick");

if ~exist(cfg.results_dir,"dir"); mkdir(cfg.results_dir); end
if ~exist(cfg.data_dir,"dir"); mkdir(cfg.data_dir); end
if ~exist(cfg.fig_dir,"dir"); mkdir(cfg.fig_dir); end

T = run_parametric_study(cfg);

disp(" ");
disp("Finished. Summary table:");
disp(T);

writetable(T, fullfile(cfg.data_dir,"study_summary.csv"));
plot_study_summary(T, cfg);

disp(" ");
disp("Results saved in results/data and results/figures.");
