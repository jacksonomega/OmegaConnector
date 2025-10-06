# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

block_cipher = None

# Añadir imports ocultos que PyInstaller no detecta automáticamente
hidden_imports = [
    'ollama',
    'ollama._client',
    'ollama._utils',
    'ollama._types',
    'flet',
    'flet.core',
    'flet.core.page',
    'fastapi',
    'fastapi.applications',
    'fastapi.routing',
    'uvicorn',
    'uvicorn.main',
    'uvicorn.server',
    'uvicorn.config',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan.on',
    'pydantic',
    'pydantic.main',
    'pydantic.fields',
    'starlette',
    'starlette.applications',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.responses',
    'starlette.routing',
    'httpx',
    'httpx._client',
    'httpx._transports',
    'httpx._transports.default',
    'asyncio',
    'threading',
    'json',
    'datetime',
    'subprocess',
    'time',
    'typing',
    'typing_extensions',
    'multipart',
    'python_multipart',
    'email.message',
    'email.parser',
    'warnings',
    'ssl',
    'certifi',
    'urllib3',
    'requests',
    'websockets',
    'h11',
    'anyio',
    'sniffio',
    'idna',
    'charset_normalizer',
]

# Obtener la ruta del sitio packages para incluir ollama
try:
    import ollama
    ollama_path = os.path.dirname(ollama.__file__)
    print(f"Ollama encontrado en: {ollama_path}")
except ImportError:
    print("ADVERTENCIA: No se pudo importar ollama")
    ollama_path = None

# Datos adicionales que necesita la aplicación
datas = []

# Si encontramos ollama, incluir sus archivos
if ollama_path:
    datas.append((ollama_path, 'ollama'))

# Incluir certificados SSL que puede necesitar httpx/ollama
try:
    import certifi
    cert_path = certifi.where()
    datas.append((cert_path, 'certifi'))
except ImportError:
    pass

# Binarios adicionales
binaries = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filtrar duplicados
a.datas = list(set(a.datas))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OmegaBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Cambiar a True si necesitas debug
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Añade tu icono aquí: icon='assets/icon.ico'
    version=None,
)
