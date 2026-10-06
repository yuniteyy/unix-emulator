#!/bin/sh
# Проверка работы с разными VFS и ошибок загрузки (этап 3).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
RUN="./run.sh"
VFS="examples/vfs"
STARTUP="examples/startup"
mkdir -p out

for name in minimal files deep; do
    echo "=== VFS: $name"
    "$RUN" --headless --vfs "$VFS/$name.xml" \
        --script "$STARTUP/stage3_vfs_load.txt"
done

echo "=== Ошибки загрузки VFS (ожидается код 1 у каждого запуска)"
for bad in missing.xml invalid/broken.xml invalid/wrong_root.xml \
        invalid/bad_base64.xml invalid/duplicate.xml; do
    echo "--- $bad"
    "$RUN" --headless --vfs "$VFS/$bad" --script "$STARTUP/basic.txt" \
        > /dev/null
    echo "код возврата: $?"
done

echo "=== vfs-save: сохранение и повторная загрузка"
for name in minimal files deep; do
    printf 'vfs-save out/%s_copy.xml\n' "$name" \
        | "$RUN" --headless --vfs "$VFS/$name.xml" > /dev/null
    "$RUN" --headless --vfs "out/${name}_copy.xml" \
        --script "$STARTUP/stage3_vfs_load.txt"
done

echo "=== Стартовый скрипт для всех команд этапа 3"
"$RUN" --headless --vfs "$VFS/deep.xml" --script "$STARTUP/stage3_all.txt"
