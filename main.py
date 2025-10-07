import asyncio
import threading
import json
import sys
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import flet as ft
import ollama
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# Función para manejar rutas de recursos cuando está compilado
def get_resource_path(relative_path):
    """Obtiene la ruta correcta para recursos, funciona tanto en desarrollo como compilado"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # En desarrollo, usa la ruta del script actual
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Configurar certificados SSL para conexiones HTTPS en ejecutables compilados
def setup_ssl_context():
    """Configura el contexto SSL para aplicaciones compiladas"""
    try:
        import ssl
        import certifi

        # Obtener la ruta de certificados
        ca_bundle = certifi.where()

        # Si está compilado, buscar certificados en el directorio temporal
        if hasattr(sys, '_MEIPASS'):
            compiled_cert_path = os.path.join(sys._MEIPASS, 'certifi', 'cacert.pem')
            if os.path.exists(compiled_cert_path):
                ca_bundle = compiled_cert_path

        # Configurar variables de entorno para SSL
        os.environ['REQUESTS_CA_BUNDLE'] = ca_bundle
        os.environ['CURL_CA_BUNDLE'] = ca_bundle

        return True
    except Exception as e:
        print(f"Warning: No se pudo configurar SSL context: {e}")
        return False

# Configurar SSL al inicio
setup_ssl_context()


# Definir paleta de colores moderna
class Colors:
    PRIMARY = "#6366f1"  # Indigo
    PRIMARY_DARK = "#4f46e5"
    SECONDARY = "#10b981"  # Emerald
    SECONDARY_DARK = "#059669"
    DANGER = "#ef4444"  # Red
    DANGER_DARK = "#dc2626"
    WARNING = "#f59e0b"  # Amber
    SURFACE = "#1e293b"  # Slate 800
    SURFACE_LIGHT = "#334155"  # Slate 700
    BACKGROUND = "#0f172a"  # Slate 900
    ON_SURFACE = "#f1f5f9"  # Slate 100
    ON_SURFACE_VARIANT = "#94a3b8"  # Slate 400


# Modelos disponibles para descargar
AVAILABLE_MODELS = [
    "qwen3:4b",
    "qwen3:8b",
    "qwen3:30b",
    "gemma3:1b",
    "gemma3:4b",
    "gemma3:12b",
    "gemma3:27b",
    "gpt-oss:20b",
    "gpt-oss:120b",
]


class ChatRequest(BaseModel):
    model: str
    prompt: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    stream: Optional[bool] = True

    class Config:
        # Permitir campos adicionales sin fallar
        extra = "allow"

    def get_messages_or_prompt(self):
        """Obtiene los mensajes o convierte el prompt a formato de mensajes"""
        if self.messages:
            return self.messages
        elif self.prompt:
            return [{"role": "user", "content": self.prompt}]
        else:
            raise ValueError("Debe proporcionar 'prompt' o 'messages'")


class OllamaManager:
    """Gestor para operaciones con Ollama"""

    @staticmethod
    def get_installed_models() -> List[str]:
        """Obtiene la lista de modelos instalados"""
        try:
            models_response = ollama.list()
            # models_response.models es una lista de objetos Model
            # Cada Model tiene un atributo 'model' con el nombre
            return [model.model for model in models_response.models]
        except Exception as e:
            print(f"Error al obtener modelos: {e}")
            return []

    @staticmethod
    async def download_model(model_name: str, progress_callback=None):
        """Descarga un modelo de Ollama usando subprocess"""
        try:
            import subprocess
            import time

            if progress_callback:
                progress_callback(f"Descargando {model_name}...")

            # Ejecutar ollama pull con codificación UTF-8
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )

            last_update = 0
            last_line = ""

            # Leer la salida línea por línea
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                # Solo actualizar cada 0.5 segundos para no saturar la UI
                current_time = time.time()
                if current_time - last_update >= 0.5 or "success" in line.lower():
                    if line != last_line and progress_callback:
                        # Filtrar líneas repetitivas o vacías
                        if any(keyword in line.lower() for keyword in ['pulling', 'downloading', 'verifying', 'success', 'digest']):
                            progress_callback(line)
                            last_update = current_time
                            last_line = line

            process.wait()

            if process.returncode == 0:
                return True, "Modelo descargado exitosamente"
            else:
                return False, f"Error al descargar modelo (código: {process.returncode})"

        except Exception as e:
            return False, f"Error al descargar modelo: {str(e)}"

    @staticmethod
    def delete_model(model_name: str):
        """Elimina un modelo de Ollama usando subprocess"""
        try:
            import subprocess

            # Ejecutar ollama rm con codificación UTF-8
            result = subprocess.run(
                ['ollama', 'rm', model_name],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                return True, "Modelo eliminado exitosamente"
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"Error al eliminar modelo: {error_msg}"

        except Exception as e:
            return False, f"Error al eliminar modelo: {str(e)}"

    @staticmethod
    async def generate_response(model: str, messages, stream: bool = True):
        """Genera una respuesta usando Ollama"""
        try:
            response = ollama.chat(
                model=model,
                messages=messages,
                stream=stream
            )

            if stream:
                for chunk in response:
                    # ollama.chat() devuelve 'message' con 'content', no 'response'
                    if 'message' in chunk:
                        content = chunk['message'].get('content', '')
                        if content:
                            yield content
            else:
                # Para no-streaming, devuelve el mensaje completo
                if 'message' in response:
                    yield response['message'].get('content', '')
        except Exception as e:
            yield f"Error: {str(e)}"

    @staticmethod
    def generate_response_sync(model: str, messages, stream: bool = True):
        """Genera una respuesta usando Ollama (versión síncrona)"""
        try:
            response = ollama.chat(
                model=model,
                messages=messages,
                stream=stream
            )

            if stream:
                for chunk in response:
                    # ollama.chat() devuelve 'message' con 'content', no 'response'
                    if 'message' in chunk:
                        content = chunk['message'].get('content', '')
                        if content:
                            yield content
            else:
                # Para no-streaming, devuelve el mensaje completo
                if 'message' in response:
                    yield response['message'].get('content', '')
        except Exception as e:
            yield f"Error: {str(e)}"


class FastAPIServer:
    """Servidor FastAPI para manejar solicitudes"""

    def __init__(self, log_callback=None):
        self.app = FastAPI(title="Omega Connector API")
        self.log_callback = log_callback
        self.server = None
        self.thread = None
        self.current_model = "qwen3:4b"

        # Configurar CORS para permitir solicitudes desde tu web
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://omega-knowledge.dev", "https://www.omega-knowledge.dev"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _log(self, message: str):
        """Registra un mensaje en el log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        if self.log_callback:
            self.log_callback(log_message)

    def _setup_routes(self):
        """Configura las rutas de la API"""

        @self.app.get("/api/health-check", status_code=status.HTTP_200_OK)
        async def root():
            self._log("GET / - Health check")
            return {"status": "online", "service": "Omega Connector"}

        @self.app.get("/models")
        async def get_models():
            self._log("GET /models - Listando modelos disponibles")
            try:
                installed = OllamaManager.get_installed_models()
                return {
                    "installed_models": installed,
                    "current_model": self.current_model
                }
            except Exception as e:
                self._log(f"ERROR: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/chat")
        async def chat(request: ChatRequest):
            # Obtener los mensajes o el prompt
            try:
                messages = request.get_messages_or_prompt()
            except ValueError as e:
                self._log(f"❌ Error: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

            # Log con información de los mensajes
            if request.messages:
                self._log(f"POST /api/chat - Model: {request.model}, Messages: {len(request.messages)} mensajes")
            else:
                self._log(f"POST /api/chat - Model: {request.model}, Prompt: {request.prompt[:50] if request.prompt else 'N/A'}...")

            try:
                if request.stream:
                    def generate():
                        # Usar el generador síncrono directamente
                        for chunk in OllamaManager.generate_response_sync(
                            request.model,
                            messages,
                            stream=True
                        ):
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                        yield "data: [DONE]\n\n"

                    return StreamingResponse(
                        generate(),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "X-Accel-Buffering": "no",
                            "Connection": "keep-alive"
                        }
                    )
                else:
                    response = ""
                    for chunk in OllamaManager.generate_response_sync(
                        request.model,
                        messages,
                        stream=False
                    ):
                        response += chunk

                    return {"response": response}
            except Exception as e:
                self._log(f"ERROR en chat: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.exception_handler(422)
        async def validation_exception_handler(request, exc):
            """Maneja errores de validación y los registra"""
            import traceback
            error_detail = str(exc)
            self._log(f"❌ Error 422 - Validación fallida: {error_detail}")

            # Intentar leer el body de la solicitud para debug
            try:
                body = await request.body()
                self._log(f"Body recibido: {body.decode('utf-8')}")
            except:
                pass

            return {
                "detail": "Error de validación. Asegúrate de enviar 'model' (string) y 'prompt' (string).",
                "error": error_detail
            }


    def start(self, host: str = "0.0.0.0", port: int = 5123):
        """Inicia el servidor FastAPI en un hilo separado con configuración mejorada para ejecutables compilados"""
        def run():
            # Configuración especial para aplicaciones compiladas
            config_args = {
                "app": self.app,
                "host": host,
                "port": port,
                "log_level": "info",
                "access_log": False,  # Desactivar logs de acceso para reducir ruido
                "use_colors": False,  # Desactivar colores en logs compilados
                "server_header": False,  # Desactivar header del servidor
                "date_header": False   # Desactivar header de fecha
            }

            # Si está compilado con PyInstaller, usar configuración específica
            if hasattr(sys, '_MEIPASS'):
                config_args.update({
                    "reload": False,
                    "workers": 1,
                    "loop": "asyncio",
                    "http": "h11"
                })

            try:
                config = uvicorn.Config(**config_args)
                self.server = uvicorn.Server(config)

                # Crear un nuevo loop de eventos para el hilo
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Ejecutar el servidor
                loop.run_until_complete(self.server.serve())

            except Exception as e:
                self._log(f"Error al iniciar servidor: {str(e)}")
                # Intentar con configuración de respaldo
                try:
                    import uvloop
                    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
                except ImportError:
                    pass  # uvloop no disponible, continuar con asyncio estándar

                # Configuración de respaldo más simple
                simple_config = uvicorn.Config(
                    self.app,
                    host=host,
                    port=port,
                    log_level="warning"
                )
                self.server = uvicorn.Server(simple_config)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.server.serve())

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        self._log(f"Servidor iniciado en http://{host}:{port}")

    def stop(self):
        """Detiene el servidor FastAPI de forma segura"""
        if self.server:
            try:
                self.server.should_exit = True
                # Dar tiempo para que el servidor se cierre correctamente
                import time
                time.sleep(0.5)
                self._log("Servidor detenido correctamente")
            except Exception as e:
                self._log(f"Error al detener servidor: {str(e)}")
                # Forzar terminación si es necesario
                if self.thread and self.thread.is_alive():
                    try:
                        self.thread.join(timeout=1.0)
                    except:
                        pass


class OmegaBridgeApp:
    """Aplicación principal de Flet"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Omega Bridge - Local LLM Server"
        self.page.window_width = 900
        self.page.window_height = 700
        self.page.padding = 20

        self.server = None
        self.server_running = False
        self.selected_model = AVAILABLE_MODELS[0]
        self.installed_models = []

        # Componentes UI
        self.status_indicator = None
        self.start_stop_btn = None
        self.model_dropdown = None
        self.download_btn = None
        self.delete_btn = None
        self.model_status_text = None
        self.log_console = None
        self.progress_bar = None
        self.progress_text = None

        self._build_ui()
        self._refresh_installed_models()

    def _log(self, message: str):
        """Añade un mensaje al log"""
        if self.log_console:
            self.log_console.value += f"{message}\n"
            self.log_console.update()

    def _build_ui(self):
        """Construye la interfaz de usuario con diseño moderno"""

        # Configurar tema de la página
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = Colors.BACKGROUND
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.padding = 30

        # Header con gradiente
        header = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.MEMORY,
                        size=50,
                        color=Colors.PRIMARY
                    ),
                ),
                ft.Column([
                    ft.Text(
                        "Omega Bridge",
                        size=36,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.ON_SURFACE,
                    ),
                    ft.Text(
                        "Local LLM Server Management",
                        size=14,
                        color=Colors.ON_SURFACE_VARIANT,
                    )
                ], spacing=0),
                ft.Container(expand=True),
                # Status badge
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=12, color=Colors.DANGER),
                        ft.Text("OFFLINE", size=12, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE)
                    ], spacing=5),
                    bgcolor=Colors.SURFACE,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border_radius=20,
                    border=ft.border.all(1, Colors.DANGER)
                )
            ], alignment=ft.MainAxisAlignment.START),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[Colors.SURFACE, Colors.SURFACE_LIGHT]
            ),
            border_radius=20,
            padding=20,
            margin=ft.margin.only(bottom=30)
        )
        self.status_badge = header.content.controls[3]

        # Server Control Card
        self.status_indicator = ft.Container(
            width=16,
            height=16,
            border_radius=8,
            bgcolor=Colors.DANGER
        )

        self.start_stop_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PLAY_ARROW, size=20, color=Colors.ON_SURFACE),
                ft.Text("Iniciar Servidor", size=14, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE)
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=Colors.SECONDARY,
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            border_radius=12,
            on_click=self._toggle_server,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color="#10b98150",
                offset=ft.Offset(0, 4)
            )
        )

        server_control = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.POWER_SETTINGS_NEW, size=24, color=Colors.PRIMARY),
                        ft.Text("Control del Servidor", size=18, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
                    ], spacing=10),
                    ft.Divider(color=Colors.SURFACE_LIGHT, height=20),
                    ft.Row([
                        self.status_indicator,
                        ft.Text("Estado: Detenido", size=14, color=Colors.ON_SURFACE_VARIANT),
                        ft.Container(expand=True),
                        self.start_stop_btn
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.LINK, size=16, color=Colors.ON_SURFACE_VARIANT),
                            ft.Text("http://localhost:5123", size=12, color=Colors.ON_SURFACE_VARIANT)
                        ], spacing=5),
                        padding=ft.padding.only(top=10)
                    )
                ], spacing=15),
                padding=25
            ),
            elevation=8,
            surface_tint_color=Colors.PRIMARY,
            color=Colors.SURFACE
        )
        self.status_text_ref = server_control.content.content.controls[2].controls[1]

        # Model Management Card
        self.model_dropdown = ft.Dropdown(
            label="Seleccionar Modelo",
            options=[ft.dropdown.Option(text=model, key=model) for model in AVAILABLE_MODELS],
            value=self.selected_model,
            on_change=self._on_model_change,
            width=320,
            bgcolor=Colors.SURFACE_LIGHT,
            border_color=Colors.PRIMARY,
            color=Colors.ON_SURFACE,
            label_style=ft.TextStyle(color=Colors.ON_SURFACE_VARIANT)
        )

        self.download_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.DOWNLOAD, size=18, color=Colors.ON_SURFACE),
                ft.Text("Descargar", size=14, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE)
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=Colors.PRIMARY,
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=10,
            on_click=self._download_model,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=6,
                color="#6366f150",
                offset=ft.Offset(0, 2)
            )
        )

        self.delete_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.DELETE_OUTLINE, size=18, color=Colors.ON_SURFACE),
                ft.Text("Eliminar", size=14, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE)
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=Colors.DANGER,
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border_radius=10,
            on_click=self._delete_model,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=6,
                color="#ef444450",
                offset=ft.Offset(0, 2)
            )
        )

        self.model_status_text = ft.Text(
            "",
            size=13,
            color=Colors.ON_SURFACE_VARIANT,
            weight=ft.FontWeight.BOLD
        )

        self.progress_bar = ft.ProgressBar(
            visible=False,
            width=400,
            color=Colors.PRIMARY,
            bgcolor=Colors.SURFACE_LIGHT
        )

        self.progress_text = ft.Text(
            "",
            size=12,
            visible=False,
            color=Colors.ON_SURFACE_VARIANT,
        )

        model_management = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SMART_TOY, size=24, color=Colors.PRIMARY),
                        ft.Text("Gestión de Modelos", size=18, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
                    ], spacing=10),
                    ft.Divider(color=Colors.SURFACE_LIGHT, height=20),
                    ft.Row([
                        self.model_dropdown,
                        ft.Container(width=10),
                        self.download_btn,
                        self.delete_btn,
                    ], spacing=10),
                    self.model_status_text,
                    self.progress_bar,
                    self.progress_text,
                ], spacing=15),
                padding=25
            ),
            elevation=8,
            surface_tint_color=Colors.PRIMARY,
            color=Colors.SURFACE
        )

        # Log Console Card
        self.log_console = ft.TextField(
            label="Console Output",
            multiline=True,
            min_lines=15,
            max_lines=15,
            read_only=True,
            value="",
            bgcolor=Colors.BACKGROUND,
            border_color=Colors.SURFACE_LIGHT,
            color=Colors.ON_SURFACE,
            label_style=ft.TextStyle(color=Colors.ON_SURFACE_VARIANT),
            text_style=ft.TextStyle(size=12)
        )

        log_section = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.TERMINAL, size=24, color=Colors.PRIMARY),
                        ft.Text("Logs del Sistema", size=18, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            icon_color=Colors.ON_SURFACE_VARIANT,
                            tooltip="Limpiar logs",
                            on_click=self._clear_logs
                        )
                    ], spacing=10),
                    ft.Divider(color=Colors.SURFACE_LIGHT, height=20),
                    self.log_console,
                ], spacing=15),
                padding=25
            ),
            elevation=8,
            surface_tint_color=Colors.PRIMARY,
            color=Colors.SURFACE
        )

        # Layout principal con scroll
        main_content = ft.Column([
            header,
            ft.Container(height=20),
            ft.Row([
                ft.Container(
                    content=server_control,
                    expand=1
                ),
                ft.Container(width=20),
                ft.Container(
                    content=model_management,
                    expand=2
                )
            ]),
            ft.Container(height=20),
            log_section,
        ], scroll=ft.ScrollMode.AUTO)

        # Añadir al página con contenedor principal
        self.page.add(
            ft.Container(
                content=main_content,
                padding=0,
                expand=True
            )
        )

        self._log("🚀 Aplicación Omega Bridge iniciada")
        self._log("📊 Interfaz moderna cargada correctamente")

    def _clear_logs(self, e):
        """Limpia la consola de logs"""
        self.log_console.value = ""
        self.log_console.update()
        self._log("🧹 Logs limpiados")

    def _refresh_installed_models(self):
        """Actualiza la lista de modelos instalados"""
        try:
            self.installed_models = OllamaManager.get_installed_models()
            self._update_model_status()
        except Exception as e:
            self._log(f"Error al obtener modelos instalados: {str(e)}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(e)}"),
                bgcolor=ft.Colors.RED_700,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _show_snackbar(self, message: str, color: str):
        """Muestra un snackbar con estilo mejorado"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=Colors.ON_SURFACE, size=20),
                ft.Text(message, color=Colors.ON_SURFACE, weight=ft.FontWeight.BOLD)
            ], spacing=10),
            bgcolor=color,
        )
        self.page.snack_bar.open = True

    def _update_model_status(self):
        """Actualiza el estado del modelo seleccionado con mejor feedback visual"""
        is_installed = any(self.selected_model in model for model in self.installed_models)

        if is_installed:
            self.model_status_text.value = f"✅ Modelo '{self.selected_model}' está instalado y listo"
            self.model_status_text.color = Colors.SECONDARY

            # Actualizar estilos de botones
            self.download_btn.disabled = True
            self.download_btn.bgcolor = Colors.SURFACE_LIGHT
            self.download_btn.content.controls[0].color = Colors.ON_SURFACE_VARIANT
            self.download_btn.content.controls[1].color = Colors.ON_SURFACE_VARIANT

            self.delete_btn.disabled = False
            self.delete_btn.bgcolor = Colors.DANGER
            self.delete_btn.content.controls[0].color = Colors.ON_SURFACE
            self.delete_btn.content.controls[1].color = Colors.ON_SURFACE
        else:
            self.model_status_text.value = f"📥 Modelo '{self.selected_model}' necesita ser descargado"
            self.model_status_text.color = Colors.WARNING

            # Actualizar estilos de botones
            self.download_btn.disabled = False
            self.download_btn.bgcolor = Colors.PRIMARY
            self.download_btn.content.controls[0].color = Colors.ON_SURFACE
            self.download_btn.content.controls[1].color = Colors.ON_SURFACE

            self.delete_btn.disabled = True
            self.delete_btn.bgcolor = Colors.SURFACE_LIGHT
            self.delete_btn.content.controls[0].color = Colors.ON_SURFACE_VARIANT
            self.delete_btn.content.controls[1].color = Colors.ON_SURFACE_VARIANT

        self.page.update()

    def _on_model_change(self, e):
        """Maneja el cambio de modelo seleccionado"""
        self.selected_model = self.model_dropdown.value
        self._update_model_status()
        self._log(f"Modelo seleccionado: {self.selected_model}")

    def _toggle_server(self, e):
        """Inicia o detiene el servidor con animaciones y feedback visual mejorado"""
        if not self.server_running:
            # Iniciar servidor
            try:
                # Animación de inicio
                self.start_stop_btn.content.controls[0].name = ft.Icons.REFRESH
                self.start_stop_btn.update()

                self.server = FastAPIServer(log_callback=self._log)
                self.server.start(host="0.0.0.0", port=5123)

                self.server_running = True

                # Actualizar UI con animaciones
                self.status_indicator.bgcolor = Colors.SECONDARY
                self.status_text_ref.value = "Estado: En ejecución"

                # Actualizar botón
                self.start_stop_btn.content.controls[0].name = ft.Icons.STOP
                self.start_stop_btn.content.controls[1].value = "Detener Servidor"
                self.start_stop_btn.bgcolor = Colors.DANGER

                # Actualizar status badge en header
                self.status_badge.content.controls[0].color = Colors.SECONDARY
                self.status_badge.content.controls[1].value = "ONLINE"
                self.status_badge.border = ft.border.all(1, Colors.SECONDARY)

                self._log("✅ Servidor FastAPI iniciado en http://0.0.0.0:5123")
                self._show_snackbar("🚀 Servidor iniciado correctamente", Colors.SECONDARY)

            except Exception as ex:
                self._log(f"❌ Error al iniciar servidor: {str(ex)}")
                self._show_snackbar(f"❌ Error al iniciar servidor: {str(ex)}", Colors.DANGER)
                # Revertir botón en caso de error
                self.start_stop_btn.content.controls[0].name = ft.Icons.PLAY_ARROW
                self.start_stop_btn.content.controls[1].value = "Iniciar Servidor"
        else:
            # Detener servidor
            try:
                if self.server:
                    self.server.stop()

                self.server_running = False

                # Actualizar UI
                self.status_indicator.bgcolor = Colors.DANGER
                self.status_text_ref.value = "Estado: Detenido"

                # Actualizar botón
                self.start_stop_btn.content.controls[0].name = ft.Icons.PLAY_ARROW
                self.start_stop_btn.content.controls[1].value = "Iniciar Servidor"
                self.start_stop_btn.bgcolor = Colors.SECONDARY

                # Actualizar status badge en header
                self.status_badge.content.controls[0].color = Colors.DANGER
                self.status_badge.content.controls[1].value = "OFFLINE"
                self.status_badge.border = ft.border.all(1, Colors.DANGER)

                self._log("⏹️ Servidor detenido")
                self._show_snackbar("⏹️ Servidor detenido", Colors.WARNING)

            except Exception as ex:
                self._log(f"❌ Error al detener servidor: {str(ex)}")

        self.page.update()

    def _download_model(self, e):
        """Descarga el modelo seleccionado"""
        self.download_btn.disabled = True
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.progress_text.value = "Iniciando descarga..."
        self.page.update()

        def progress_callback(status):
            self.progress_text.value = status
            self._log(f"Descarga: {status}")
            self.page.update()

        async def download():
            self._log(f"Iniciando descarga de modelo: {self.selected_model}")
            success, message = await OllamaManager.download_model(
                self.selected_model,
                progress_callback
            )

            self.progress_bar.visible = False
            self.progress_text.visible = False
            self.download_btn.disabled = False

            if success:
                self._log(f"✅ {message}")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.GREEN_700,
                )
                self._refresh_installed_models()
            else:
                self._log(f"❌ {message}")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(message),
                    bgcolor=ft.Colors.RED_700,
                )

            self.page.snack_bar.open = True
            self.page.update()

        # Ejecutar descarga en un hilo separado
        threading.Thread(target=lambda: asyncio.run(download()), daemon=True).start()

    def _delete_model(self, e):
        """Elimina el modelo seleccionado con diálogo mejorado"""
        def confirm_delete(confirmed):
            dialog.open = False
            self.page.update()

            if confirmed:
                self._log(f"🗑️ Eliminando modelo: {self.selected_model}")
                success, message = OllamaManager.delete_model(self.selected_model)

                if success:
                    self._log(f"✅ {message}")
                    self._show_snackbar(f"✅ {message}", Colors.SECONDARY)
                    self._refresh_installed_models()
                else:
                    self._log(f"❌ {message}")
                    self._show_snackbar(f"❌ {message}", Colors.DANGER)

        # Diálogo moderno con mejor estilo
        dialog = ft.AlertDialog(
            bgcolor=Colors.SURFACE,
            title=ft.Text(
                "⚠️ Confirmar eliminación",
                color=Colors.ON_SURFACE,
                size=18,
                weight=ft.FontWeight.BOLD
            ),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        f"¿Estás seguro de que deseas eliminar el modelo:",
                        color=Colors.ON_SURFACE_VARIANT,
                        size=14
                    ),
                    ft.Container(
                        content=ft.Text(
                            self.selected_model,
                            color=Colors.PRIMARY,
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=Colors.SURFACE_LIGHT,
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border_radius=8,
                        margin=ft.margin.symmetric(vertical=10)
                    ),
                    ft.Text(
                        "Esta acción no se puede deshacer.",
                        color=Colors.DANGER,
                        size=12,
                        italic=True
                    )
                ], spacing=5),
                width=300
            ),
            actions=[
                ft.Container(
                    content=ft.Text("Cancelar", color=Colors.ON_SURFACE_VARIANT),
                    bgcolor=Colors.SURFACE_LIGHT,
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    border_radius=8,
                    on_click=lambda _: confirm_delete(False)
                ),
                ft.Container(
                    content=ft.Text("Eliminar", color=Colors.ON_SURFACE, weight=ft.FontWeight.BOLD),
                    bgcolor=Colors.DANGER,
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    border_radius=8,
                    on_click=lambda _: confirm_delete(True)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()


def main(page: ft.Page):
    OmegaBridgeApp(page)


if __name__ == "__main__":
    ft.app(target=main)
