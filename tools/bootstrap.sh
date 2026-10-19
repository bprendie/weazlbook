#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"
if [ ! -x .bootstrap/bin/uv ]; then
 python3 -m venv .bootstrap
 .bootstrap/bin/pip install uv==0.13.1
fi
if [ ! -x .venv/bin/python ]; then .bootstrap/bin/uv venv --python 3.12 .venv; fi
.bootstrap/bin/uv pip install --python .venv/bin/python -r requirements.lock.txt
if [ ! -d .toolchains/esp-idf ]; then
 git clone --depth 1 --branch v5.5.6 --recursive --shallow-submodules https://github.com/espressif/esp-idf.git .toolchains/esp-idf
fi
test "$(git -C .toolchains/esp-idf rev-parse HEAD)" = 880a203ae603d08a94d06aa01e0d6761958e5e9e
export IDF_TOOLS_PATH="$project_root/.toolchains/espressif"
# Run tool installer with the underlying interpreter, not from a virtualenv.
base_python=$(readlink -f .venv/bin/python)
"$base_python" .toolchains/esp-idf/tools/idf_tools.py install --targets esp32s3
"$base_python" .toolchains/esp-idf/tools/idf_tools.py install-python-env
