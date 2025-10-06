@echo off
echo ========================================
echo  Omega Bridge - Compilacion Avanzada
echo ========================================
echo.

echo [1/6] Verificando entorno virtual...
if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo [2/6] Actualizando pip...
python -m pip install --upgrade pip

echo.
echo [3/6] Instalando dependencias base...
pip install wheel setuptools

echo.
echo [4/6] Instalando dependencias del proyecto...
pip install -r requirements.txt

echo.
echo [5/6] Instalando PyInstaller...
pip install pyinstaller

echo.
echo [6/6] Compilando con configuracion especial para ollama...
pyinstaller --clean --noconfirm ^
    --add-data "venv\Lib\site-packages\ollama;ollama" ^
    --hidden-import ollama ^
    --hidden-import ollama._client ^
    --hidden-import ollama._utils ^
    --hidden-import flet ^
    --hidden-import fastapi ^
    --hidden-import uvicorn ^
    --hidden-import pydantic ^
    --hidden-import httpx ^
    --collect-all ollama ^
    --collect-all flet ^
    --onefile ^
    --windowed ^
    --name OmegaBridge ^
    main.py

if %errorlevel% neq 0 (
    echo ERROR: Fallo en la compilacion avanzada
    echo Intentando con el archivo .spec...
    pyinstaller main.spec
)

echo.
if exist dist\OmegaBridge.exe (
    echo ========================================
    echo        COMPILACION COMPLETADA!
    echo ========================================
    echo El ejecutable esta en: dist\OmegaBridge.exe
) else (
    echo ========================================
    echo         ERROR EN COMPILACION
    echo ========================================
    echo Revisa los logs arriba para mas detalles
)

echo.
pause
