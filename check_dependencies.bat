@echo off
echo ========================================
echo   Diagnostico de Dependencias Ollama
echo ========================================
echo.

echo [1/4] Verificando instalacion de Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado
    pause
    exit /b 1
)

echo.
echo [2/4] Verificando pip...
pip --version

echo.
echo [3/4] Verificando dependencias instaladas...
echo Verificando ollama...
python -c "import ollama; print(f'Ollama version: {ollama.__version__ if hasattr(ollama, \"__version__\") else \"N/A\"}')"
if %errorlevel% neq 0 (
    echo ERROR: ollama no instalado o no funciona
    echo Instalando ollama...
    pip install ollama
)

echo Verificando flet...
python -c "import flet; print(f'Flet version: {flet.__version__ if hasattr(flet, \"__version__\") else \"N/A\"}')"

echo Verificando fastapi...
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"

echo Verificando uvicorn...
python -c "import uvicorn; print(f'Uvicorn version: {uvicorn.__version__}')"

echo.
echo [4/4] Probando importaciones del main.py...
python -c "
try:
    import sys
    print('Probando importaciones...')
    import ollama
    print('✓ ollama')
    import flet as ft
    print('✓ flet')
    import fastapi
    print('✓ fastapi')
    import uvicorn
    print('✓ uvicorn')
    import pydantic
    print('✓ pydantic')
    print('Todas las importaciones exitosas!')
except ImportError as e:
    print(f'ERROR de importacion: {e}')
    sys.exit(1)
"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Hay problemas con las dependencias
    echo Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo   DIAGNOSTICO COMPLETADO - TODO OK
echo ========================================
echo Ahora puedes ejecutar build.bat o build_advanced.bat
pause
