function save_current_figure(filename)
%SAVE_CURRENT_FIGURE Saves PNG and FIG version of current figure.

[folder,base,~] = fileparts(filename);
if ~exist(folder,"dir"); mkdir(folder); end

saveas(gcf, fullfile(folder, base + ".png"));
savefig(gcf, fullfile(folder, base + ".fig"));
end
