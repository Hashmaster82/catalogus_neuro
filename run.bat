@echo off
chcp 65001 >nul
title Catalogus Neuro

setlocal enabledelayedexpansion

echo ================================
echo     Catalogus Neuro Launcher
echo ================================
echo.

:CHECK_UPDATES
:: Проверка наличия Git
git --version >nul 2>&1
if errorlevel 1 (
    echo Git не установлен. Проверка обновлений невозможна.
    goto CHECK_PYTHON
)

echo Проверка обновлений из репозитория...

:: Получаем текущую ветку
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set CURRENT_BRANCH=%%i

if "!CURRENT_BRANCH!"=="" (
    echo Репозиторий не инициализирован. Пропуск проверки обновлений.
    goto CHECK_PYTHON
)

:: Проверяем наличие обновлений
git fetch origin >nul 2>&1

set LOCAL_COMMIT=
set REMOTE_COMMIT=

for /f "tokens=*" %%i in ('git rev-parse HEAD 2^>nul') do set LOCAL_COMMIT=%%i
for /f "tokens=*" %%i in ('git rev-parse origin/!CURRENT_BRANCH! 2^>nul') do set REMOTE_COMMIT=%%i

if "!LOCAL_COMMIT!"=="!REMOTE_COMMIT!" (
    echo Версия актуальна.
) else (
    echo.
    echo ========== ДОСТУПНО ОБНОВЛЕНИЕ! ==========
    echo Текущая версия: !LOCAL_COMMIT:~0,8!
    echo Новая версия:   !REMOTE_COMMIT:~0,8!
    echo.

    :: Показываем список изменений
    echo Последние изменения:
    git log --oneline !LOCAL_COMMIT!..origin/!CURRENT_BRANCH! --color=never 2>nul

    echo.
    choice /C YN /M "Обновить сейчас (Y - Да, N - Нет)"
    if !errorlevel! equ 1 (
        echo.
        echo Выполняется обновление...
        git pull origin !CURRENT_BRANCH!
        if !errorlevel! equ 0 (
            echo Обновление завершено успешно!
            echo Рекомендуется перезапустить приложение.
            echo.
            choice /C YN /M "Перезапустить сейчас"
            if !errorlevel! equ 1 (
                echo Перезапуск...
                goto RESTART
            )
        ) else (
            echo ОШИБКА при обновлении!
        )
    )
)

:CHECK_PYTHON
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не установлен или не добавлен в PATH
    echo Установите Python с официального сайта:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Виртуальное окружение
if exist "venv\" (
    echo Активация виртуального окружения...
    call venv\Scripts\activate
) else (
    echo Создание виртуального окружения...
    python -m venv venv
    call venv\Scripts\activate
    echo Установка зависимостей...
    pip install -r requirements.txt
)

:: Обновление зависимостей
echo Проверка зависимостей...
pip install --upgrade -r requirements.txt

:: Запуск приложения
echo.
echo ================================
echo    Запуск Catalogus Neuro...
echo ================================
echo.

python app.py

:: После закрытия приложения
echo.
choice /C YNR /M "Действие: (Y) Перезапуск, (N) Выход, (R) Проверить обновления"
if !errorlevel! equ 1 goto RESTART
if !errorlevel! equ 2 exit /b 0
if !errorlevel! equ 3 goto CHECK_UPDATES

:RESTART
echo.
echo Перезапуск приложения...
timeout /t 2 /nobreak >nul
call "%~f0"