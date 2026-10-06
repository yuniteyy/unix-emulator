#!/bin/sh
# Проверка всех параметров командной строки (этап 2).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/run.sh"
STARTUP="$ROOT/examples/startup"

echo "=== 1. Только --script"
"$RUN" --headless --script "$STARTUP/basic.txt"

echo "=== 2. --prompt"
"$RUN" --headless --prompt "user@host> " --script "$STARTUP/basic.txt"

echo "=== 3. --vfs (на этапе 2 путь только выводится в отладке)"
"$RUN" --headless --vfs "$ROOT/examples/vfs/minimal.xml" \
    --script "$STARTUP/basic.txt"

echo "=== 4. Все параметры вместе"
"$RUN" --headless --vfs "$ROOT/examples/vfs/minimal.xml" \
    --prompt "[{vfs}] {cwd} \$ " --script "$STARTUP/basic.txt"

echo "=== 5. Скрипт с ошибочными строками"
"$RUN" --headless --script "$STARTUP/errors.txt"

echo "=== 6. exit внутри скрипта"
"$RUN" --headless --script "$STARTUP/with_exit.txt"

echo "=== 7. Несуществующий скрипт (ожидается ошибка)"
"$RUN" --headless --script "$STARTUP/missing.txt"
echo "код возврата: $?"
