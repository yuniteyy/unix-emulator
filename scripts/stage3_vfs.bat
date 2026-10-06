@echo off
setlocal enabledelayedexpansion
rem Проверка работы с разными VFS и ошибок загрузки (этап 3).
set "ROOT=%~dp0..\"
cd /d "%ROOT%"
set "VFS=examples\vfs"
set "STARTUP=examples\startup"
if not exist out mkdir out

for %%N in (minimal files deep) do (
    echo === VFS: %%N
    call run.bat --headless --vfs "%VFS%\%%N.xml" --script "%STARTUP%\stage3_vfs_load.txt"
)

echo === Ошибки загрузки VFS (ожидается код 1 у каждого запуска)
for %%B in (missing.xml invalid\broken.xml invalid\wrong_root.xml invalid\bad_base64.xml invalid\duplicate.xml) do (
    echo --- %%B
    call run.bat --headless --vfs "%VFS%\%%B" --script "%STARTUP%\basic.txt" > nul
    echo код возврата: !ERRORLEVEL!
)

echo === vfs-save: сохранение и повторная загрузка
for %%N in (minimal files deep) do (
    echo vfs-save out\%%N_copy.xml| call run.bat --headless --vfs "%VFS%\%%N.xml" > nul
    call run.bat --headless --vfs "out\%%N_copy.xml" --script "%STARTUP%\stage3_vfs_load.txt"
)

echo === Стартовый скрипт для всех команд этапа 3
call run.bat --headless --vfs "%VFS%\deep.xml" --script "%STARTUP%\stage3_all.txt"
