@echo off
rem Проверка команд ls, cd, echo, cat на разных VFS (этап 4).
set "ROOT=%~dp0..\"
cd /d "%ROOT%"
set "VFS=examples\vfs"
set "STARTUP=examples\startup"
if not exist out mkdir out

echo === Все команды этапа 4 на deep.xml
call run.bat --headless --vfs "%VFS%\deep.xml" --script "%STARTUP%\stage4_all.txt"

echo === Минимальная VFS: ls, cat
(echo ls -l& echo cat readme.txt& echo cat missing.txt) | call run.bat --headless --vfs "%VFS%\minimal.xml"

echo === Несколько файлов: -a, текст, двоичный файл
(echo ls -a& echo cat notes.txt& echo cat logo.bin) | call run.bat --headless --vfs "%VFS%\files.xml"

echo === Пустая VFS без --vfs
(echo ls& echo cd /x& echo echo ok) | call run.bat --headless

echo === vfs-save не меняет содержимое: сравнение вывода
call run.bat --headless --vfs "%VFS%\deep.xml" --script "%STARTUP%\stage4_dump.txt" > out\dump_original.txt
echo vfs-save out\deep_copy.xml| call run.bat --headless --vfs "%VFS%\deep.xml" > nul
call run.bat --headless --vfs out\deep_copy.xml --script "%STARTUP%\stage4_dump.txt" > out\dump_copy.txt
rem Строки [debug] отличаются путём к VFS, поэтому сравниваются только строки диалога.
findstr /V /B /C:"[debug]" out\dump_original.txt > out\dump_original_clean.txt
findstr /V /B /C:"[debug]" out\dump_copy.txt > out\dump_copy_clean.txt
fc out\dump_original_clean.txt out\dump_copy_clean.txt && echo OK: содержимое идентично
