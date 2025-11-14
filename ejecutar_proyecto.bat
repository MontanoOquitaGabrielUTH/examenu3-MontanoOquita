@echo off
REM Script para ejecutar el proyecto Django de forma rápida
REM Guarda este archivo y haz doble clic para ejecutar

echo ============================================
echo    SISTEMA DE TIENDA - DJANGO + MYSQL
echo ============================================
echo.

REM Verificar si existe la carpeta del proyecto
if not exist "manage.py" (
    echo ERROR: No se encuentra manage.py
    echo Asegurate de ejecutar este archivo en la carpeta del proyecto
    pause
    exit
)

echo [1/3] Verificando instalacion de Django...
python -c "import django" 2>nul
if errorlevel 1 (
    echo.
    echo Django no esta instalado. Instalando dependencias...
    pip install django mysqlclient
)

echo.
echo [2/3] Aplicando migraciones a la base de datos...
python manage.py migrate

echo.
echo [3/3] Iniciando servidor de desarrollo...
echo.
echo ============================================
echo   Servidor corriendo en:
echo   http://localhost:8000/
echo.
echo   Para detener: presiona Ctrl+C
echo ============================================
echo.

REM Abrir navegador automaticamente
start http://localhost:8000/

REM Ejecutar servidor
python manage.py runserver

pause
