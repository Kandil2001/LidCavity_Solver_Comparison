function export_case_csv(result,case_name,cfg)
%EXPORT_CASE_CSV Write residual history and, optionally, field CSV data.
%
% For large HPC data-first runs, set cfg.export_fields = false. This keeps
% the residual history CSV but avoids writing large field dumps for every case.

if ~exist(cfg.data_dir,"dir")
    mkdir(cfg.data_dir);
end

if ~isfield(cfg,'export_fields') || cfg.export_fields
    field_path = fullfile(cfg.data_dir, [case_name '_fields.csv']);
    fid = fopen(field_path,'w');
    if fid < 0
        error('Could not open %s for writing.', field_path);
    end
    fprintf(fid,'i,j,x,y,u,v,p,speed,vorticity\n');
    for i = 1:result.N
        for j = 1:result.N
            fprintf(fid,'%d,%d,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g\n', ...
                i-1,j-1,result.x(j),result.y(i),result.u(i,j),result.v(i,j), ...
                result.p(i,j),result.speed(i,j),result.vorticity(i,j));
        end
    end
    fclose(fid);
end

history_path = fullfile(cfg.data_dir, [case_name '_history.csv']);
fid = fopen(history_path,'w');
if fid < 0
    error('Could not open %s for writing.', history_path);
end
fprintf(fid,'iter,Ru,Rv,Rc_mass,Rc_div,dt,poisson_iters,poisson_relative_residual,poisson_converged\n');
for k = 1:numel(result.Ru)
    fprintf(fid,'%d,%.12g,%.12g,%.12g,%.12g,%.12g,%d,%.12g,%d\n', ...
        k,result.Ru(k),result.Rv(k),result.Rc_mass(k),result.Rc_div(k), ...
        result.dt(k),result.poisson_iters(k),result.poisson_relative_residual(k), ...
        result.poisson_converged(k));
end
fclose(fid);
end
