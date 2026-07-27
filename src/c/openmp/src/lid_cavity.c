/*
 * Modular C lid-driven cavity solver.
 *
 * The original single-file source was split into small source fragments so the
 * project reads closer to the MATLAB version: data/config, operators, solver,
 * validation/output, and CLI are separated. They are included into one
 * translation unit to keep the build simple on university clusters.
 */

#include "common/common.c"
#include "core/matrix.c"
#include "core/operators.c"
#include "core/solver.c"
#include "post/validation_and_output.c"
#include "app/cli.c"
