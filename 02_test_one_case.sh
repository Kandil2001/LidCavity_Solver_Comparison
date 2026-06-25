#!/bin/bash
set -euo pipefail
cd ~/LidCavity_Solver_Comparison
mkdir -p logs
cat > jobs/test_one_case.sbatch <<'EOT'
#!/bin/bash
#SBATCH --job-name=test_one_case
#SBATCH --output=logs/test_one_case_%j.out
#SBATCH --error=logs/test_one_case_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
bash jobs/run_one_case_isolated.sh c_serial 1 1
EOT
jid=$(sbatch --parsable jobs/test_one_case.sbatch)
echo "Test job: $jid"
echo "After it finishes, run:"
echo "  cat logs/test_one_case_${jid}.out"
echo "  cat logs/test_one_case_${jid}.err"
echo "  ls -lh comparison/results/split/c_serial_case_001.csv"
