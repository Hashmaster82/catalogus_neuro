@echo off
chcp 65001 >nul
title Catalogus Neuro

echo ================================
echo     Catalogus Neuro Launcher
echo ================================
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

:: Проверка наличия виртуального окружения
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

:: Проверка наличия requirements.txt
if not exist "requirements.txt" (
    echo ОШИБКА: Файл requirements.txt не найден
    pause
    exit /b 1
)

:: Проверка и установка зависимостей
echo Проверка зависимостей...
pip install -r requirements.txt

:: Запуск приложения
echo.
echo ================================
echo    Запуск Catalogus Neuro...
echo ================================
echo.

python app.py

:: Пауза после закрытия приложения
echo.
echo Приложение закрыто.
pause