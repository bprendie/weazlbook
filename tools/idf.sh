#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export IDF_PATH="$project_root/.toolchains/esp-idf"
export IDF_TOOLS_PATH="$project_root/.toolchains/espressif"
export PATH="$project_root/.venv/bin:$PATH"
source "$IDF_PATH/export.sh" >/dev/null
cd "$project_root/firmware"
exec idf.py "$@"
