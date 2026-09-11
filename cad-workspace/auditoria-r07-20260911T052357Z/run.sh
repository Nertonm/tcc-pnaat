#!/bin/sh
set -eu
cd "$(dirname "$0")"
SR=$HOME/.cache/qwen-mm-plugins/apps/freecad-1.1.1/squashfs-root
export LD_LIBRARY_PATH="$SR/usr/lib/x86_64-linux-gnu:$SR/usr/lib"
export QT_PLUGIN_PATH="$SR/usr/lib/x86_64-linux-gnu/qt5/plugins"
"$SR/usr/bin/freecadcmd" "$PWD/build.py"
"$SR/usr/bin/freecadcmd" "$PWD/verify.py"
python3 "$PWD/section-summary.py"
