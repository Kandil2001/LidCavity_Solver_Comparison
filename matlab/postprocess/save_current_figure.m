function save_current_figure(filename)
%SAVE_CURRENT_FIGURE Saves PNG and, when available, MATLAB FIG version.

[folder,base,~] = fileparts(filename);
if ~exist(folder,'dir'); mkdir(folder); end

saveas(gcf, fullfile(folder, [base '.png']));

% GNU Octave does not support MATLAB .fig files in the same way.  PNG is the
% portable output used on clusters; MATLAB users still get .fig files.
if exist('is_octave_runtime','file') && is_octave_runtime()
    return;
end

if exist('savefig','file')
    savefig(gcf, fullfile(folder, [base '.fig']));
end
end
