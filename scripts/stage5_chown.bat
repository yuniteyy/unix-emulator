@echo off
rem Проверка команды chown и сохранения результата (этап 5).
set "ROOT=%~dp0..\"
cd /d "%ROOT%"
set "VFS=examples\vfs"
set "STARTUP=examples\startup"
if not exist out mkdir out

copy /Y "%VFS%\deep.xml" out\deep_before.xml > nul
echo === Все режимы chown на deep.xml
call run.bat --headless --vfs "%VFS%\deep.xml" --script "%STARTUP%\stage5_all.txt"

echo === Исходный XML не изменился (правки только в памяти)
fc /B "%VFS%\deep.xml" out\deep_before.xml > nul && echo OK || echo ОШИБКА: исходный файл изменён

echo === Загрузка файла, сохранённого через vfs-save
(echo ls -l /home/alice/docs& echo ls -l /home/bob& echo ls -l /etc) | call run.bat --headless --vfs out\chown_result.xml

echo === chown на VFS с несколькими файлами
(echo chown -R nobody:nogroup /& echo ls -l) | call run.bat --headless --vfs "%VFS%\files.xml"

echo === chown на минимальной VFS и на пустой
(echo chown guest readme.txt& echo ls -l) | call run.bat --headless --vfs "%VFS%\minimal.xml"
(echo chown guest x) | call run.bat --headless
