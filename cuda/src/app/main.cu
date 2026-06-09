int main(int argc, char** argv) {
    RunConfig cfg = parse_args(argc, argv);
    int N=cfg.N, nn=N*N;
    double dx = cfg.L / double(N-1);
    double nu = cfg.U * cfg.L / double(cfg.Re);
    double dt = choose_dt(N, cfg.Re, cfg);
    int block=cfg.blockSize, grid=(nn+block-1)/block, gridN=(N+block-1)/block;
    double *u,*v,*p,*us,*vs,*rhs,*phi,*phi2,*speed,*vort;
    CUDA_CHECK(cudaMalloc(&u, nn*sizeof(double))); CUDA_CHECK(cudaMalloc(&v, nn*sizeof(double))); CUDA_CHECK(cudaMalloc(&p, nn*sizeof(double)));
    CUDA_CHECK(cudaMalloc(&us, nn*sizeof(double))); CUDA_CHECK(cudaMalloc(&vs, nn*sizeof(double))); CUDA_CHECK(cudaMalloc(&rhs, nn*sizeof(double)));
    CUDA_CHECK(cudaMalloc(&phi, nn*sizeof(double))); CUDA_CHECK(cudaMalloc(&phi2, nn*sizeof(double))); CUDA_CHECK(cudaMalloc(&speed, nn*sizeof(double))); CUDA_CHECK(cudaMalloc(&vort, nn*sizeof(double)));
    init_fields<<<grid,block>>>(u,v,p,N,cfg.U); CUDA_CHECK(cudaMemset(phi,0,nn*sizeof(double))); CUDA_CHECK(cudaDeviceSynchronize());
    cudaEvent_t start, stop; CUDA_CHECK(cudaEventCreate(&start)); CUDA_CHECK(cudaEventCreate(&stop)); CUDA_CHECK(cudaEventRecord(start));
    int use_upwind = (cfg.scheme != "central");
    for (int it=0; it<cfg.maxIter; ++it) {
        momentum_kernel<<<grid,block>>>(u,v,p,us,vs,N,dx,dt,nu,cfg.alpha_u,use_upwind);
        apply_bc<<<gridN,block>>>(us,vs,nullptr,N,cfg.U);
        divergence_rhs_kernel<<<grid,block>>>(us,vs,rhs,N,dx,dt);
        CUDA_CHECK(cudaMemset(phi,0,nn*sizeof(double)));
        for (int k=0; k<cfg.poissonIter; ++k) {
            jacobi_kernel<<<grid,block>>>(phi,phi2,rhs,N,dx);
            apply_bc<<<gridN,block>>>(us,vs,phi2,N,cfg.U);
            std::swap(phi, phi2);
        }
        correct_kernel<<<grid,block>>>(u,v,p,us,vs,phi,N,dx,dt,cfg.alpha_p);
        apply_bc<<<gridN,block>>>(u,v,p,N,cfg.U);
    }
    derived_kernel<<<grid,block>>>(u,v,p,speed,vort,N,dx);
    CUDA_CHECK(cudaEventRecord(stop)); CUDA_CHECK(cudaEventSynchronize(stop));
    float ms=0.0f; CUDA_CHECK(cudaEventElapsedTime(&ms,start,stop));
    std::vector<double> hu(nn), hv(nn), hp(nn), hs(nn), hw(nn);
    CUDA_CHECK(cudaMemcpy(hu.data(),u,nn*sizeof(double),cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(hv.data(),v,nn*sizeof(double),cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(hp.data(),p,nn*sizeof(double),cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(hs.data(),speed,nn*sizeof(double),cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(hw.data(),vort,nn*sizeof(double),cudaMemcpyDeviceToHost));
    write_outputs(cfg, ms/1000.0, hu,hv,hp,hs,hw);
    std::cout << "CUDA run finished. Summary: results/data/study_summary_cuda.csv\n";
    cudaFree(u); cudaFree(v); cudaFree(p); cudaFree(us); cudaFree(vs); cudaFree(rhs); cudaFree(phi); cudaFree(phi2); cudaFree(speed); cudaFree(vort);
    return 0;
}
