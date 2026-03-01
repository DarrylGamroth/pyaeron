#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AERON_SRC="${1:-$ROOT_DIR/../aeron}"
BUILD_DIR="${2:-$AERON_SRC/cmake-build}"

if [[ ! -d "$AERON_SRC" ]]; then
  echo "Aeron source directory not found: $AERON_SRC" >&2
  echo "Usage: $0 [aeron-source-dir] [build-dir]" >&2
  exit 1
fi

cmake -S "$AERON_SRC" -B "$BUILD_DIR"

if command -v nproc >/dev/null 2>&1; then
  JOBS="$(nproc)"
elif command -v sysctl >/dev/null 2>&1; then
  JOBS="$(sysctl -n hw.ncpu)"
else
  JOBS=4
fi

cmake --build "$BUILD_DIR" --target aeron --parallel "$JOBS"
echo "Built libaeron target in: $BUILD_DIR"

