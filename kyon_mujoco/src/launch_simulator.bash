#!/usr/bin/env bash
set -euo pipefail

args=()
for arg in "$@"; do
    if [[ -n "${arg//[[:space:]]/}" ]]; then
        args+=("$arg")
    fi
done

exec python3 -m xbot2_py_mujoco.simulate "${args[@]}"
