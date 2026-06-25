function run_one_case_from_env()
%RUN_ONE_CASE_FROM_ENV Run one MATLAB/Octave case using environment variables.

addpath('src/app');
addpath('src/core');
addpath('src/studies');
addpath('src/validation');
addpath('postprocess');

N = str2double(getenv('LID_N'));
Re = str2double(getenv('LID_RE'));
scheme = getenv('LID_SCHEME');
pressure_solver = getenv('LID_PRESSURE');
implementation = getenv('LID_IMPLEMENTATION');

cfg = default_config('full');
cfg.meshes = N;
cfg.re_list = Re;
cfg.schemes = {scheme};
cfg.pressure_solvers = {pressure_solver};
cfg.implementations = {implementation};
cfg.make_figures = false;
cfg.figure_every_case = false;
cfg.export_fields = false;
cfg.export_csv = true;

if ~exist(cfg.results_dir,'dir'); mkdir(cfg.results_dir); end
if ~exist(cfg.data_dir,'dir'); mkdir(cfg.data_dir); end
if isfield(cfg,'fig_dir') && ~exist(cfg.fig_dir,'dir'); mkdir(cfg.fig_dir); end

T = run_parametric_study(cfg);
if isstruct(T) && isfield(T,'headers') && isfield(T,'rows')
    write_cell_csv(fullfile(cfg.data_dir, 'study_summary_single.csv'), T.headers, T.rows);
else
    writetable(T, fullfile(cfg.data_dir, 'study_summary_single.csv'));
end
end
