@echo off
rem Проверка всех параметров командной строки (этап 2).
set "ROOT=%~dp0..\"
set "STARTUP=%ROOT%examples\startup"

echo === 1. Только --script
call "%ROOT%run.bat" --headless --script "%STARTUP%\basic.txt"

echo === 2. --prompt
call "%ROOT%run.bat" --headless --prompt "user@host> " --script "%STARTUP%\basic.txt"

echo === 3. --vfs
call "%ROOT%run.bat" --headless --vfs "%ROOT%examples\vfs\minimal.xml" --script "%STARTUP%\basic.txt"

echo === 4. Все параметры вместе
call "%ROOT%run.bat" --headless --vfs "%ROOT%examples\vfs\minimal.xml" --prompt "[{vfs}] {cwd} $ " --script "%STARTUP%\basic.txt"

echo === 5. Скрипт с ошибочными строками
call "%ROOT%run.bat" --headless --script "%STARTUP%\errors.txt"

echo === 6. exit внутри скрипта
call "%ROOT%run.bat" --headless --script "%STARTUP%\with_exit.txt"

echo === 7. Несуществующий скрипт (ожидается ошибка)
call "%ROOT%run.bat" --headless --script "%STARTUP%\missing.txt"
echo код возврата: %ERRORLEVEL%
