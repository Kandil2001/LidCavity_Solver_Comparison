function T = run_mode_app(mode)
%RUN_MODE_APP Compatibility target used by the root-level run_mode.m wrapper.
%
% The normal Makefile workflow still uses run_mode.m inside src/app.

if nargin < 1
    mode = "quick";
end

T = run_mode(mode);
end
