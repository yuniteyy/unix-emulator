#!/bin/sh
# Запуск всех проверочных скриптов подряд.
DIR="$(cd "$(dirname "$0")" && pwd)"
for script in stage2_params stage3_vfs stage4_commands stage5_chown; do
    echo "################ $script"
    "$DIR/$script.sh" || exit 1
done
