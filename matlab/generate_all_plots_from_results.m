function generate_all_plots_from_results()
%GENERATE_ALL_PLOTS_FROM_RESULTS Create figures for every saved MATLAB benchmark case.
%
% Run this AFTER run_full_benchmark_compare.* has finished.
% It does not rerun the solver; it only loads saved .mat files from
% results/data and creates plots in results/figures.

clc; close all;

addpath("core");
addpath("studies");
addpath("validation");
addpath("post");

cfg = default_config("full");
cfg.make_figures = true;
cfg.figure_every_case = true;
cfg.export_csv = true;
cfg.results_dir = "results";
cfg.data_dir = fullfile("results","data");
cfg.fig_dir = fullfile("results","figures");

if ~exist(cfg.data_dir,"dir")
    error("No MATLAB results/data folder found. Run the full benchmark first.");
end
if ~exist(cfg.fig_dir,"dir"); mkdir(cfg.fig_dir); end

files = dir(fullfile(cfg.data_dir, "case_*.mat"));
if isempty(files)
    error("No saved MATLAB case_*.mat files found in %s. Run the full benchmark first.", cfg.data_dir);
end

fprintf("\nGenerating MATLAB plots for %d saved cases...\n", numel(files));

for k = 1:numel(files)
    case_file = fullfile(files(k).folder, files(k).name);
    [~, case_name, ~] = fileparts(case_file);
    S = load(case_file);

    if ~isfield(S,"result")
        warning("Skipping %s because it does not contain result.", files(k).name);
        continue;
    end

    fprintf("[%03d/%03d] Plotting %s\n", k, numel(files), case_name);

    plot_residuals(S.result,cfg,case_name);
    plot_fields(S.result,cfg,case_name);
    plot_validation(S.result,cfg,case_name);
end

summary_csv = fullfile(cfg.data_dir, "study_summary_full_matlab.csv");
if exist(summary_csv,"file")
    T = readtable(summary_csv);
    plot_study_summary(T,cfg);
end

fprintf("\nFinished. MATLAB figures are in %s\n", cfg.fig_dir);
end
