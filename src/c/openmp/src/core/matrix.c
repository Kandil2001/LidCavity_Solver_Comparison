/* -------------------------------------------------------------------------
 * Matrix helpers
 * ------------------------------------------------------------------------- */

static Matrix matrix_new(int n, double value) {
    Matrix m;
    m.n = n;
    m.a = (double*)malloc((size_t)n * (size_t)n * sizeof(double));
    if (!m.a) die("Out of memory");
    #pragma omp parallel for schedule(static)
    for (int k = 0; k < n * n; ++k) m.a[k] = value;
    return m;
}

static Matrix matrix_copy(const Matrix *src) {
    Matrix m = matrix_new(src->n, 0.0);
    memcpy(m.a, src->a, (size_t)src->n * (size_t)src->n * sizeof(double));
    return m;
}

static void matrix_free(Matrix *m) {
    free(m->a);
    m->a = NULL;
    m->n = 0;
}

static double max_abs_matrix(const Matrix *m) {
    double r = 0.0;
    int nn = m->n * m->n;
    #pragma omp parallel for reduction(max:r) schedule(static)
    for (int k = 0; k < nn; ++k) {
        double v = fabs(m->a[k]);
        if (v > r) r = v;
    }
    return r;
}

static double mean_matrix(const Matrix *m) {
    double s = 0.0;
    int nn = m->n * m->n;
    if (nn == 0) return 0.0;
    #pragma omp parallel for reduction(+:s) schedule(static)
    for (int k = 0; k < nn; ++k) s += m->a[k];
    return s / (double)nn;
}

static int all_finite_matrix(const Matrix *m) {
    int nn = m->n * m->n;
    for (int k = 0; k < nn; ++k) if (!isfinite(m->a[k])) return 0;
    return 1;
}

