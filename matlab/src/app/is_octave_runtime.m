function tf = is_octave_runtime()
%IS_OCTAVE_RUNTIME True when the code is running in GNU Octave.
%
% The repository keeps one MATLAB/Octave-compatible source tree.  This small
% helper is used only for features that are not equally available in both
% runtimes, such as MATLAB table output or .fig saving.

tf = exist('OCTAVE_VERSION','builtin') ~= 0;
end
