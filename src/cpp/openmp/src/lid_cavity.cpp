/*
 * Modular C++ lid-driven cavity solver.
 *
 * The code is split in the same spirit as the MATLAB repository: common data,
 * operators, solver loop, validation/output, and CLI live in separate files.
 * The fragments are included into one translation unit to keep the Makefile
 * portable and simple.
 */

#include "common/common.cpp"
#include "core/operators.cpp"
#include "core/solver.cpp"
#include "post/validation.cpp"
#include "post/output.cpp"
#include "app/cli.cpp"
