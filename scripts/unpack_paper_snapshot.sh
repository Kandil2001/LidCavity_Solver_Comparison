#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/unpack_paper_snapshot.sh ARCHIVE.tar.gz [DESTINATION_PARENT]

Example:
  bash scripts/unpack_paper_snapshot.sh \
    ~/uploads/lidcavity-paper-snapshot-20260724T080000Z.tar.gz \
    /beegfs/kandil/paper_runs

This script does not call Git. It verifies the optional SHA-256 sidecar when
present, extracts the snapshot into a timestamped directory, and prints the
resulting run path.
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

archive=$(readlink -f "$1")
destination_parent=${2:-"${HOME}/paper_runs"}

if [[ ! -f "$archive" ]]; then
  echo "Archive not found: $archive" >&2
  exit 1
fi

mkdir -p "$destination_parent"
destination_parent=$(readlink -f "$destination_parent")

checksum_file="${archive}.sha256"
if [[ -f "$checksum_file" ]]; then
  echo "Verifying checksum: $checksum_file"
  (
    cd "$(dirname "$archive")"
    sha256sum -c "$(basename "$checksum_file")"
  )
else
  echo "Warning: checksum sidecar not found; extraction will continue." >&2
fi

stamp=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="${destination_parent}/LidCavity_Paper_${stamp}"
mkdir -p "$run_dir"

tar -xzf "$archive" -C "$run_dir" --strip-components=1

mkdir -p \
  "$run_dir/comparison/results/toolchain" \
  "$run_dir/comparison/results/paper_v1/raw" \
  "$run_dir/comparison/results/paper_v1/processed" \
  "$run_dir/logs"

echo
printf 'Snapshot extracted to:\n  %s\n' "$run_dir"
echo "No Git repository or Git metadata is present or required."
echo
echo "Next safe check:"
printf '  cd %q\n' "$run_dir"
echo "  bash scripts/check_paper_toolchain.sh --output comparison/results/toolchain/stromboli.txt"
