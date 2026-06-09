/*
 * Modular CUDA lid-driven cavity solver.
 *
 * CUDA kernels, run configuration, output, CLI, and main loop are split into
 * separate files. They are included into one .cu translation unit so `nvcc` can
 * compile the project with the simple Makefile.
 */

#include "common/common.cu"
#include "kernels/kernels.cu"
#include "app/config.cu"
#include "post/output.cu"
#include "app/cli.cu"
#include "app/main.cu"
