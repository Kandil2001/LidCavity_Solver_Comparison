#!/bin/bash
set -euo pipefail

PREFIX="$HOME/software/miniforge3"
ENVNAME="lid_env"

mkdir -p "$HOME/software"

if [ ! -f "$PREFIX/etc/profile.d/conda.sh" ]; then
    echo "Miniforge not found. Installing into $PREFIX"
    cd "$HOME/software"
    if [ ! -f Miniforge3-Linux-x86_64.sh ]; then
        if command -v wget >/dev/null 2>&1; then
            wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
        elif command -v curl >/dev/null 2>&1; then
            curl -L -o Miniforge3-Linux-x86_64.sh https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
        else
            echo "No wget/curl found. Download Miniforge3-Linux-x86_64.sh manually into ~/software and rerun this script."
            exit 1
        fi
    fi
    bash Miniforge3-Linux-x86_64.sh -b -p "$PREFIX"
fi

source "$PREFIX/etc/profile.d/conda.sh"

if ! conda env list | awk '{print $1}' | grep -qx "$ENVNAME"; then
    conda create -n "$ENVNAME" -c conda-forge python=3.10 octave numpy pandas matplotlib mpi4py -y
else
    conda install -n "$ENVNAME" -c conda-forge python=3.10 octave numpy pandas matplotlib mpi4py -y
fi

conda activate "$ENVNAME"
python --version
octave --version | head -5
python -c "import mpi4py; print('mpi4py ok')"
