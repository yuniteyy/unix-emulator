#!/bin/sh
# Проверка команды chown и сохранения результата (этап 5).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
RUN="./run.sh"
VFS="examples/vfs"
STARTUP="examples/startup"
mkdir -p out

BEFORE="$(cksum < "$VFS/deep.xml")"
echo "=== Все режимы chown на deep.xml"
"$RUN" --headless --vfs "$VFS/deep.xml" --script "$STARTUP/stage5_all.txt"

echo "=== Исходный XML не изменился (правки только в памяти)"
AFTER="$(cksum < "$VFS/deep.xml")"
if [ "$BEFORE" = "$AFTER" ]; then
    echo "OK"
else
    echo "ОШИБКА: исходный файл изменён"
    exit 1
fi

echo "=== Загрузка файла, сохранённого через vfs-save"
printf 'ls -l /home/alice/docs\nls -l /home/bob\nls -l /etc\n' \
    | "$RUN" --headless --vfs out/chown_result.xml

echo "=== chown на VFS с несколькими файлами"
printf 'chown -R nobody:nogroup /\nls -l\n' \
    | "$RUN" --headless --vfs "$VFS/files.xml"

echo "=== chown на минимальной VFS и на пустой"
printf 'chown guest readme.txt\nls -l\n' \
    | "$RUN" --headless --vfs "$VFS/minimal.xml"
printf 'chown guest x\n' | "$RUN" --headless
