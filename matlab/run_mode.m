function T = run_mode(mode)
%RUN_MODE Compatibility entry point for running from the matlab/ folder.
%
% The maintained app workflow lives in src/app. This root-level file is kept
% only so users can type run_mode('quick') after opening the matlab folder.

if nargin < 1
    mode = "quick";
end

addpath("src/app");
addpath("src/core");
addpath("src/studies");
addpath("src/validation");
addpath("postprocess");

T = run_mode_app(mode);
end
