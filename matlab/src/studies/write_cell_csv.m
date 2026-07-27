function write_cell_csv(filename, headers, rows)
%WRITE_CELL_CSV Small table-free CSV writer that works in MATLAB and Octave.

[folder,~,~] = fileparts(filename);
if ~isempty(folder) && ~exist(folder,'dir')
    mkdir(folder);
end

fid = fopen(filename, 'w');
if fid < 0
    error('Could not open %s for writing.', filename);
end

for j = 1:numel(headers)
    if j > 1; fprintf(fid, ','); end
    fprintf(fid, '%s', csv_escape(headers{j}));
end
fprintf(fid, '\n');

for i = 1:size(rows,1)
    for j = 1:numel(headers)
        if j > 1; fprintf(fid, ','); end
        fprintf(fid, '%s', csv_escape(rows{i,j}));
    end
    fprintf(fid, '\n');
end

fclose(fid);
end

function s = csv_escape(value)
if isnumeric(value)
    if isempty(value)
        s = '';
    elseif isscalar(value)
        if isnan(value)
            s = 'NaN';
        elseif isinf(value)
            if value > 0
                s = 'Inf';
            else
                s = '-Inf';
            end
        elseif abs(value - round(value)) < 1e-12 && abs(value) < 1e12
            s = sprintf('%.0f', value);
        else
            s = sprintf('%.12g', value);
        end
    else
        s = mat2str(value);
    end
elseif islogical(value)
    s = sprintf('%d', value ~= 0);
elseif ischar(value)
    s = value;
else
    try
        s = char(value);
    catch
        s = '';
    end
end

if any(s == ',') || any(s == '"') || any(s == sprintf('\n')) || any(s == sprintf('\r'))
    s = ['"' strrep(s, '"', '""') '"'];
end
end
