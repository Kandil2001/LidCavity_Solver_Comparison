% MAIN ENTRY POINT
% Same-setup MATLAB/Octave lid-driven cavity study.
%
% Run from MATLAB or Octave:
%   main                 % quick mode
%   run_quick
%   run_medium
%   run_full

clear; clc; close all;

addpath('src/app');
addpath('src/core');
addpath('src/studies');
addpath('src/validation');
addpath('postprocess');

cfg = default_config('quick');
if is_octave_runtime() && ~strcmp(getenv('OCTAVE_MAKE_FIGURES'),'1')
    cfg.make_figures = false;
    cfg.figure_every_case = false;
end

if ~exist(cfg.results_dir,'dir'); mkdir(cfg.results_dir); end
if ~exist(cfg.data_dir,'dir'); mkdir(cfg.data_dir); end
if ~exist(cfg.fig_dir,'dir'); mkdir(cfg.fig_dir); end

T = run_parametric_study(cfg);

disp(' ');
disp('Finished. Summary:');
disp(T);

if cfg.make_figures && ~(isstruct(T) && isfield(T,'rows'))
    plot_study_summary(T, cfg);
end

disp(' ');
disp('Results saved in results/data and results/figures.');
