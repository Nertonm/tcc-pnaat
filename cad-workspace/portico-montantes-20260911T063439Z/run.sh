#!/bin/sh
# Reproducible run. Do not install anything; uses the existing FreeCAD 1.1.1
# console build inside the qwen-mm-plugins squashfs root.
set -e
SR=$HOME/.cache/qwen-mm-plugins/apps/freecad-1.1.1/squashfs-root
D=$(cd "$(dirname "$0")" && pwd)
runuser -u nerton -- env \
  LD_LIBRARY_PATH=$SR/usr/lib/x86_64-linux-gnu:$SR/usr/lib \
  QT_PLUGIN_PATH=$SR/usr/lib/x86_64-linux-gnu/qt5/plugins \
  $SR/usr/bin/freecadcmd "$@"
