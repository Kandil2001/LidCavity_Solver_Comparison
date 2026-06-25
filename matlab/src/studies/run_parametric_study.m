function T = run_parametric_study(cfg)
%RUN_PARAMETRIC_STUDY Runs mesh, Re, scheme, solver, implementation study.
%
% The function writes the same CSV summary in both MATLAB and GNU Octave.
% In MATLAB it also returns a table. In Octave it returns a lightweight
% struct with headers and rows because Octave installations on clusters often
% do not include MATLAB's table/writetable functionality.

rows = {};
case_id = 0;

for iN = 1:numel(cfg.meshes)
    N = cfg.meshes(iN);

    for iR = 1:numel(cfg.re_list)
        Re = cfg.re_list(iR);

        for is = 1:numel(cfg.schemes)
            scheme = cfg.schemes{is};

            for ip = 1:numel(cfg.pressure_solvers)
                pressure_solver = cfg.pressure_solvers{ip};

                for ii = 1:numel(cfg.implementations)
                    implementation = cfg.implementations{ii};

                    case_id = case_id + 1;
                    case_name = sprintf('case_%03d_N%d_Re%d_%s_%s_%s', ...
                        case_id,N,Re,scheme,pressure_solver,implementation);

                    fprintf('\n[%03d] N=%d Re=%d Scheme=%s Pressure=%s Implementation=%s\n', ...
                        case_id,N,Re,scheme,pressure_solver,implementation);

                    result = solve_lid_cavity(N,Re,scheme,pressure_solver,implementation,cfg);
                    metrics = validate_against_ghia(result);

                    quality = quality_label_matlab(result,metrics);

                    fprintf('      status=%s quality=%s iter=%d/%d Rc_mass=%.3e Rc_div=%.3e runtime=%.2fs avgPiter=%.1f\n', ...
                        result.status,quality,result.iterations,result.localMaxIter,result.final_Rc_mass,result.final_Rc_div,result.runtime,result.avg_poisson_iters);

                    save(fullfile(cfg.data_dir, [case_name '.mat']), 'result', 'metrics');

                    if isfield(cfg,'export_csv') && cfg.export_csv
                        export_case_csv(result,case_name,cfg);
                    end

                    if cfg.make_figures && cfg.figure_every_case
                        plot_residuals(result,cfg,case_name);
                        plot_fields(result,cfg,case_name);
                        plot_validation(result,cfg,case_name);
                    end

                    rows(end+1,:) = { ...
                        case_id, ...
                        char(implementation), ...
                        N, ...
                        Re, ...
                        char(scheme), ...
                        char(pressure_solver), ...
                        char(result.status), ...
                        char(quality), ...
                        result.iterations, ...
                        result.localMaxIter, ...
                        result.final_Ru, ...
                        result.final_Rv, ...
                        result.final_Rc_mass, ...
                        result.final_Rc_div, ...
                        result.runtime, ...
                        result.avg_poisson_iters, ...
                        result.avg_poisson_relative_residual, ...
                        result.pressure_saturation_ratio, ...
                        metrics.available, ...
                        metrics.available && metrics.u_L2 <= get_ghia_limit(result.Re,'u') && metrics.v_L2 <= get_ghia_limit(result.Re,'v'), ...
                        metrics.u_L2, ...
                        metrics.v_L2, ...
                        metrics.u_Linf, ...
                        metrics.v_Linf, ...
                        get_ghia_limit(result.Re,'u'), ...
                        get_ghia_limit(result.Re,'v')};
                end
            end
        end
    end
end

headers = { ...
    'CaseID','Implementation','N','Re','Scheme','PressureSolver','Status','Quality', ...
    'Iterations','LocalMaxIter','FinalRu','FinalRv','FinalRcMass','FinalRcDiv','Runtime_s', ...
    'AvgPoissonIterations','AvgPoissonRelResidual','PressureSaturationRatio', ...
    'HasGhia','ValidationPass','Ghia_u_L2','Ghia_v_L2','Ghia_u_Linf','Ghia_v_Linf', ...
    'Ghia_u_L2_Limit','Ghia_v_L2_Limit'};

write_cell_csv(fullfile(cfg.data_dir, 'study_summary.csv'), headers, rows);

if exist('is_octave_runtime','file') && is_octave_runtime()
    T.headers = headers;
    T.rows = rows;
else
    T = cell2table(rows, 'VariableNames', headers);
end

save(fullfile(cfg.data_dir, 'study_summary.mat'), 'T');
end

function quality = quality_label_matlab(result,metrics)
if strcmp(result.status,'converged') && metrics.available && ...
        metrics.u_L2 <= get_ghia_limit(result.Re,'u') && metrics.v_L2 <= get_ghia_limit(result.Re,'v')
    quality = 'converged_validated';
elseif strcmp(result.status,'converged') && metrics.available
    quality = 'converged_not_validated';
elseif strcmp(result.status,'converged') && ~metrics.available
    quality = 'converged_no_benchmark';
elseif ~strcmp(result.status,'converged') && metrics.available && ...
        metrics.u_L2 <= get_ghia_limit(result.Re,'u') && metrics.v_L2 <= get_ghia_limit(result.Re,'v')
    quality = 'validated_but_not_converged';
else
    quality = 'needs_improvement';
end
end

function limit = get_ghia_limit(Re,component)
if Re == 100
    limit = 0.030;
elseif Re == 400
    if component == 'u'
        limit = 0.090;
    else
        limit = 0.120;
    end
elseif Re == 1000
    if component == 'u'
        limit = 0.160;
    else
        limit = 0.180;
    end
else
    limit = inf;
end
end
