"""
Omega Connector - FastAPI Bridge to Ollama
Modern GUI application with logging and server management
"""

#Ollama URL: https://github.com/ollama/ollama/releases/download/v0.12.0/OllamaSetup.exe

import flet as ft
import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import requests
import json

# --- Configuration ---
CONFIG = {
    "TOKEN": "usuario123",
    "OLLAMA_URL": "http://localhost:11434/api/chat",
    "HOST": "127.0.0.1",
    "PORT": 5123,
    "ORIGINS": ["https://omega-knowledge.vercel.app", "http://localhost:4200"]
}


# --- Simple Log Handler ---
class SimpleLogHandler:
    def __init__(self):
        self.logs: List[str] = []
        self.callbacks: List[callable] = []

    def add_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_log = f"[{timestamp}] {message}"
        self.logs.append(formatted_log)

        # Keep only last 50 logs
        if len(self.logs) > 50:
            self.logs.pop(0)

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(formatted_log)
            except Exception:
                pass

    def add_callback(self, callback: callable) -> None:
        self.callbacks.append(callback)


# Global log handler
log_handler = SimpleLogHandler()

# --- FastAPI Application ---
app = FastAPI(
    title="Omega Connector",
    description="Bridge entre Omega Knowledge y Ollama local",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG["ORIGINS"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()

    # Log request
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    log_handler.add_log(f"📥 {method} {url} desde {client_ip}")

    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    status_code = response.status_code
    status_emoji = "✅" if status_code < 400 else "❌"
    log_handler.add_log(f"📤 {status_emoji} {status_code} - {process_time:.3f}s")

    return response

@app.get('/api/health-check')
async def health_check_endpoint():
    """Simple health check endpoint"""
    return {"status": "ok"}

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Proxy chat requests to local Ollama with streaming support"""
    try:
        # Get payload
        payload = await request.json()
        model = payload.get('model', 'unknown')
        is_streaming = payload.get('stream', False)

        log_handler.add_log(f"🤖 Enviando petición a Ollama: {model} (stream: {is_streaming})")

        # Forward to Ollama
        response = requests.post(
            CONFIG["OLLAMA_URL"],
            json=payload,
            timeout=60,
            stream=is_streaming  # Enable streaming if requested
        )

        if response.status_code == 200:
            if is_streaming:
                log_handler.add_log("🌊 Iniciando respuesta streaming de Ollama")

                def generate_stream():
                    try:
                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                # Forward each chunk as received
                                yield f"{decoded_line}\n"
                    except Exception as e:
                        log_handler.add_log(f"💥 Error en streaming: {str(e)}")
                        error_response = {
                            "error": str(e)
                        }
                        yield f"data: {json.dumps(error_response)}\n\n"

                return StreamingResponse(
                    generate_stream(),
                    media_type="text/plain",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    }
                )
            else:
                log_handler.add_log("🎯 Respuesta de Ollama recibida exitosamente")
                return response.json()
        else:
            log_handler.add_log(f"💥 Error de Ollama: {response.status_code}")
            raise HTTPException(
                status_code=502,
                detail=f"Error de Ollama: {response.status_code}"
            )

    except requests.exceptions.ConnectionError:
        log_handler.add_log("🔌 No se puede conectar con Ollama")
        raise HTTPException(
            status_code=502,
            detail="No se puede conectar con Ollama. ¿Está corriendo?"
        )
    except Exception as e:
        log_handler.add_log(f"💥 Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# --- Server Manager ---
class ServerManager:
    def __init__(self):
        self.server_thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        self.server = None

    def start_server(self) -> bool:
        """Start the FastAPI server"""
        if self.is_running:
            log_handler.add_log("⚠️ El servidor ya está corriendo")
            return False

        try:
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            self.is_running = True
            log_handler.add_log("🟢 Servidor iniciado correctamente")
            return True

        except Exception as e:
            log_handler.add_log(f"💥 Error al iniciar servidor: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop the FastAPI server"""
        if not self.is_running:
            log_handler.add_log("⚠️ El servidor no está corriendo")
            return False

        try:
            self.is_running = False
            if self.server:
                self.server.should_exit = True
            log_handler.add_log("🔴 Servidor detenido")
            return True

        except Exception as e:
            log_handler.add_log(f"💥 Error al detener servidor: {e}")
            return False

    def _run_server(self) -> None:
        """Run the FastAPI server"""
        log_handler.add_log("🚀 Iniciando Omega Connector...")
        log_handler.add_log(f"📡 Servidor disponible en http://{CONFIG['HOST']}:{CONFIG['PORT']}")

        config = uvicorn.Config(
            app,
            host=CONFIG["HOST"],
            port=CONFIG["PORT"],
            log_level="warning"  # Reduce uvicorn logs
        )
        self.server = uvicorn.Server(config)
        self.server.run()


# --- GUI Application ---
class OmegaConnectorApp:
    def __init__(self):
        self.server_manager = ServerManager()
        self.log_container: Optional[ft.ListView] = None
        self.status_text: Optional[ft.Text] = None
        self.start_button: Optional[ft.ElevatedButton] = None
        self.stop_button: Optional[ft.ElevatedButton] = None

    def create_gui(self, page: ft.Page) -> None:
        """Create the main GUI"""
        # Page configuration
        page.title = "Omega Connector"
        page.window_width = 600
        page.window_height = 500
        page.window_resizable = False
        page.padding = 20
        page.theme_mode = ft.ThemeMode.DARK

        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CABLE, color="orange", size=30),
                ft.Text(
                    "Omega Connector",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color="orange"
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            margin=ft.margin.only(bottom=20)
        )

        # Status section
        self.status_text = ft.Text(
            "🔴 Servidor detenido",
            size=16,
            weight=ft.FontWeight.W_500,
            color="white"
        )

        status_container = ft.Container(
            content=self.status_text,
            padding=15,
            bgcolor="#2c2c2c",
            border_radius=10,
            margin=ft.margin.only(bottom=15)
        )

        # Control buttons
        self.start_button = ft.ElevatedButton(
            "🚀 Iniciar Servidor",
            on_click=self._start_server,
            bgcolor="green",
            color="white",
            width=140
        )

        self.stop_button = ft.ElevatedButton(
            "Detener Servidor",
            on_click=self._stop_server,
            bgcolor="red",
            color="white",
            width=140,
            disabled=True
        )

        buttons_row = ft.Row([
            self.start_button,
            self.stop_button
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)

        # Logs section
        logs_title = ft.Text(
            "📋 Logs del Sistema",
            size=16,
            weight=ft.FontWeight.BOLD,
            color="white"
        )

        self.log_container = ft.ListView(
            height=250,
            spacing=2,
            padding=10,
            auto_scroll=True
        )

        logs_container = ft.Container(
            content=self.log_container,
            bgcolor="#2c2c2c",
            border_radius=10,
            padding=5
        )

        # Add components to page
        page.add(
            header,
            status_container,
            buttons_row,
            ft.Container(height=20),  # Spacer
            logs_title,
            logs_container
        )

        # Setup log callback
        log_handler.add_callback(self._add_log_entry)

        # Add initial log
        log_handler.add_log("🎯 Omega Connector inicializado")

    def _start_server(self, e: ft.ControlEvent) -> None:
        """Handle start server button click"""
        if self.server_manager.start_server():
            self._update_ui_state(True)

    def _stop_server(self, e: ft.ControlEvent) -> None:
        """Handle stop server button click"""
        if self.server_manager.stop_server():
            self._update_ui_state(False)

    def _update_ui_state(self, server_running: bool) -> None:
        """Update UI based on server state"""
        if server_running:
            self.status_text.value = f"🟢 Servidor activo en http://{CONFIG['HOST']}:{CONFIG['PORT']}"
            self.status_text.color = "green"
            self.start_button.disabled = True
            self.stop_button.disabled = False
        else:
            self.status_text.value = "🔴 Servidor detenido"
            self.status_text.color = "red"
            self.start_button.disabled = False
            self.stop_button.disabled = True

        page = self.status_text.page
        if page:
            page.update()

    def _add_log_entry(self, log_message: str) -> None:
        """Add a new log entry to the GUI"""
        if self.log_container:
            log_item = ft.Text(
                log_message,
                size=12,
                color="lightgray",
                font_family="Consolas"
            )
            self.log_container.controls.append(log_item)

            # Keep only last 50 entries
            if len(self.log_container.controls) > 50:
                self.log_container.controls.pop(0)

            try:
                page = self.log_container.page
                if page:
                    page.update()
            except Exception:
                pass


def main() -> None:
    app_instance = OmegaConnectorApp()

    def handle_window_event(e):
        if e.data == "close":
            log_handler.add_log("🔄 Cerrando aplicación...")
            if app_instance.server_manager.is_running:
                app_instance.server_manager.stop_server()
            e.page.window_destroy()

    def setup_window(page: ft.Page):
        page.on_window_event = handle_window_event
        app_instance.create_gui(page)

    ft.app(target=setup_window)


if __name__ == "__main__":
    main()