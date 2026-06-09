/*
 * CUDA lid-driven cavity solver.
 *
 * This is a GPU-focused benchmark implementation using a projection-style
 * finite-difference method on a collocated uniform grid. It intentionally keeps
 * the same command-line style and CSV output columns as the CPU repos so the
 * comparison repo can read its summaries.
 *
 * Numerical note: the CUDA implementation uses Jacobi pressure iterations
 * because Jacobi maps naturally to GPU kernels. The CPU repos also offer RBGS
 * and RBSOR; here --pressure is accepted for CLI compatibility but the kernel
 * reports cuda_jacobi_pressure_projection in the Implementation column.
 */
#include <cuda_runtime.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <filesystem>
#include <chrono>

namespace fs = std::filesystem;

#define CUDA_CHECK(call) do { \
    cudaError_t err__ = (call); \
    if (err__ != cudaSuccess) { \
        std::fprintf(stderr, "CUDA error %s:%d: %s\n", __FILE__, __LINE__, cudaGetErrorString(err__)); \
        std::exit(1); \
    } \
} while (0)

__host__ __device__ inline int idx(int i, int j, int N) { return i * N + j; }

