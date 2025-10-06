@echo off
echo ========================================
echo  Omega Bridge - Script de Compilacion
echo ========================================
echo.

echo [1/5] Instalando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Fallo al instalar dependencias
    pause
    exit /b 1
)

echo.
echo [2/5] Instalando PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo ERROR: Fallo al instalar PyInstaller
    pause
    exit /b 1
)

echo.
echo [3/5] Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo [4/5] Compilando aplicacion...
pyinstaller main.spec
if %errorlevel% neq 0 (
    echo ERROR: Fallo en la compilacion
    echo.
    echo Intentando compilacion con modo debug...
    pyinstaller --debug=all main.spec
    pause
    exit /b 1
)

echo.
echo [5/5] Compilacion completada!
echo El ejecutable se encuentra en: dist\OmegaBridge.exe
echo.
echo ========================================
echo            COMPILACION EXITOSA
echo ========================================
pause
