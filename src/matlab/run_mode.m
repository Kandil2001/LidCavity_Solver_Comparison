function T = run_mode(mode)
%RUN_MODE Compatibility entry point for running from the matlab/ folder.
addpath('src/app');
T = run_mode_app(mode);
end
