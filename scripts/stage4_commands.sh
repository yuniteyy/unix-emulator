#!/bin/sh
# Проверка команд ls, cd, echo, cat на разных VFS (этап 4).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
RUN="./run.sh"
VFS="examples/vfs"
STARTUP="examples/startup"
mkdir -p out

echo "=== Все команды этапа 4 на deep.xml"
"$RUN" --headless --vfs "$VFS/deep.xml" --script "$STARTUP/stage4_all.txt"

echo "=== Минимальная VFS: ls, cat"
printf 'ls -l\ncat readme.txt\ncat missing.txt\n' \
    | "$RUN" --headless --vfs "$VFS/minimal.xml"

echo "=== Несколько файлов: -a, текст, двоичный файл"
printf 'ls -a\nls -l\ncat notes.txt\ncat data.csv\ncat logo.bin\n' \
    | "$RUN" --headless --vfs "$VFS/files.xml"

echo "=== Пустая VFS без --vfs"
printf 'ls\ncd /x\ncat y\necho ok\n' | "$RUN" --headless

echo "=== vfs-save не меняет содержимое: сравнение вывода"
"$RUN" --headless --vfs "$VFS/deep.xml" --script "$STARTUP/stage4_dump.txt" \
    | grep -v '^\[debug\]' > out/dump_original.txt
printf 'vfs-save out/deep_copy.xml\n' \
    | "$RUN" --headless --vfs "$VFS/deep.xml" > /dev/null
"$RUN" --headless --vfs out/deep_copy.xml --script "$STARTUP/stage4_dump.txt" \
    | grep -v '^\[debug\]' > out/dump_copy.txt
if diff out/dump_original.txt out/dump_copy.txt; then
    echo "OK: содержимое идентично"
else
    echo "ОШИБКА: содержимое отличается"
    exit 1
fi
