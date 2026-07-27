#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

typedef struct {
    int N;
    int Re;
    const char *scheme;
    const char *pressure;
    const char *implementation;
} CaseDef;

static void mkdir_p(const char *path) {
    char tmp[PATH_MAX];
    snprintf(tmp, sizeof(tmp), "%s", path);
    for (char *p = tmp + 1; *p; ++p) {
        if (*p == '/') { *p = 0; mkdir(tmp, 0775); *p = '/'; }
    }
    mkdir(tmp, 0775);
}

static int build_cases(const char *mode, CaseDef *cases, int max_cases) {
    int meshes[3] = {32, 64, 128}; int n_mesh = 3;
    int res[3] = {100, 400, 1000}; int n_re = 3;
    const char *schemes[2] = {"upwind", "central"}; int n_scheme = 2;
    const char *pressures[2] = {"RBGS", "RBSOR"}; int n_pressure = 2;
    const char *impls[1] = {"serial_cpp"}; int n_impl = 1;

    if (strcmp(mode, "smoke") == 0) { meshes[0] = 16; n_mesh = 1; res[0] = 100; n_re = 1; n_scheme = 1; n_pressure = 1; }
    else if (strcmp(mode, "quick") == 0) { n_mesh = 2; n_re = 2; }
    else if (strcmp(mode, "medium") == 0) { n_mesh = 2; n_re = 3; }
    else if (strcmp(mode, "full") == 0) { }
    else { fprintf(stderr, "Unknown mode: %s\n", mode); MPI_Abort(MPI_COMM_WORLD, 2); }

    int n = 0;
    for (int a = 0; a < n_mesh; ++a)
    for (int b = 0; b < n_re; ++b)
    for (int c = 0; c < n_scheme; ++c)
    for (int d = 0; d < n_pressure; ++d)
    for (int e = 0; e < n_impl; ++e) {
        if (n >= max_cases) return n;
        cases[n++] = (CaseDef){meshes[a], res[b], schemes[c], pressures[d], impls[e]};
    }
    return n;
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank = 0, size = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    const char *mode = "quick";
    const char *solver = "./bin/lid_cavity";
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--mode") == 0 && i + 1 < argc) mode = argv[++i];
        else if (strcmp(argv[i], "--solver") == 0 && i + 1 < argc) solver = argv[++i];
    }

    char root[PATH_MAX];
    if (!getcwd(root, sizeof(root))) { perror("getcwd"); MPI_Abort(MPI_COMM_WORLD, 3); }
    char solver_abs[PATH_MAX];
    if (solver[0] == '/') snprintf(solver_abs, sizeof(solver_abs), "%s", solver);
    else snprintf(solver_abs, sizeof(solver_abs), "%s/%s", root, solver);

    CaseDef cases[512];
    int ncases = build_cases(mode, cases, 512);
    if (rank == 0) printf("MPI case-parallel C++ driver: %d cases over %d ranks\n", ncases, size);

    for (int case_id = rank; case_id < ncases; case_id += size) {
        CaseDef c = cases[case_id];
        char workdir[PATH_MAX];
        snprintf(workdir, sizeof(workdir), "%s/results/mpi_raw/rank_%03d/case_%03d", root, rank, case_id + 1);
        mkdir_p(workdir);
        char cmd[PATH_MAX * 2];
        snprintf(cmd, sizeof(cmd),
                 "cd '%s' && '%s' --single --N %d --Re %d --scheme %s --pressure %s --implementation %s --no-fields",
                 workdir, solver_abs, c.N, c.Re, c.scheme, c.pressure, c.implementation);
        printf("[rank %d] case %03d: N=%d Re=%d %s %s %s\n", rank, case_id + 1, c.N, c.Re, c.scheme, c.pressure, c.implementation);
        int rc = system(cmd);
        if (rc != 0) fprintf(stderr, "[rank %d] command failed for case %d with rc=%d\n", rank, case_id + 1, rc);
    }

    MPI_Barrier(MPI_COMM_WORLD);
    if (rank == 0) printf("Done. Run: python3 scripts/merge_mpi_results.py\n");
    MPI_Finalize();
    return 0;
}
