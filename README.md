# Omega Bridge - Local LLM Server

Aplicación desktop que permite gestionar y ejecutar modelos LLM locales usando Ollama, con un servidor FastAPI para integración con aplicaciones web.

## Características

- 🖥️ **Interfaz gráfica con Flet**: Interfaz amigable y moderna
- 🚀 **Servidor FastAPI**: API REST con soporte para streaming
- 🤖 **Integración con Ollama**: Gestión completa de modelos LLM locales
- 📊 **Consola de logs**: Monitoreo en tiempo real de solicitudes
- 🔄 **Descarga/Eliminación de modelos**: Gestión fácil de modelos
- 🌐 **CORS habilitado**: Listo para integración con tu web

## Instalación

1. **Instalar Ollama**:
   - Descarga e instala Ollama desde: https://ollama.ai
   - Asegúrate de que Ollama esté en ejecución

2. **Instalar dependencias de Python**:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. **Ejecutar la aplicación**:
   ```bash
   python main.py
   ```

2. **Gestionar modelos**:
   - Selecciona un modelo del dropdown
   - Haz clic en "Descargar Modelo" para instalarlo
   - Una vez instalado, puedes eliminarlo con "Eliminar Modelo"

3. **Iniciar el servidor**:
   - Haz clic en "Iniciar Servidor"
   - El servidor estará disponible en `http://localhost:8000`

## API Endpoints

### `GET /`
Health check del servidor.

### `GET /models`
Obtiene la lista de modelos instalados.

```json
{
  "installed_models": ["llama3.2:3b", "mistral:7b"],
  "current_model": "llama3.2:3b"
}
```

### `POST /chat`
Realiza una consulta al modelo LLM.

**Request:**
```json
{
  "model": "llama3.2:3b",
  "prompt": "¿Qué es la inteligencia artificial?",
  "stream": true
}
```

**Response (streaming):**
```
data: {"chunk": "La "}
data: {"chunk": "inteligencia "}
data: {"chunk": "artificial..."}
data: [DONE]
```

### `POST /set-model`
Cambia el modelo activo.

**Request:**
```json
{
  "model": "mistral:7b"
}
```

## Integración con tu Web

Desde `omega-knowledge.dev`, puedes hacer solicitudes al servidor:

### Ejemplo con JavaScript (Streaming):

```javascript
async function askQuestion(prompt, model = "llama3.2:3b") {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: model,
      prompt: prompt,
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          console.log('Streaming completado');
          return;
        }
        
        try {
          const parsed = JSON.parse(data);
          console.log(parsed.chunk); // Procesar cada fragmento
        } catch (e) {
          // Ignorar líneas malformadas
        }
      }
    }
  }
}

// Uso
askQuestion("Explícame qué es React");
```

### Ejemplo con fetch (Sin streaming):

```javascript
async function askQuestionNoStream(prompt, model = "llama3.2:3b") {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: model,
      prompt: prompt,
      stream: false
    })
  });

  const data = await response.json();
  return data.response;
}
```

## Modelos Disponibles

- llama3.2:3b (3B parámetros)
- llama3.2:1b (1B parámetros)
- llama3.1:8b (8B parámetros)
- mistral:7b (7B parámetros)
- phi3:mini
- gemma2:2b (2B parámetros)
- qwen2.5:7b (7B parámetros)
- codellama:7b (especializado en código)

## Notas de Seguridad

- En producción, configura CORS específicamente para tu dominio en lugar de `allow_origins=["*"]`
- Considera agregar autenticación si el servidor estará expuesto públicamente
- Los modelos se ejecutan localmente, manteniendo tu privacidad

## Requisitos del Sistema

- Python 3.8+
- Ollama instalado y en ejecución
- 8GB+ RAM (dependiendo del modelo)
- Espacio en disco para modelos (1-7GB por modelo)

## Troubleshooting

**Error: "Connection refused"**
- Asegúrate de que Ollama esté en ejecución
- Verifica que no haya otro servicio en el puerto 8000

**Error al descargar modelos**
- Verifica tu conexión a internet
- Asegúrate de tener suficiente espacio en disco

**El servidor no inicia**
- Verifica que el puerto 8000 no esté en uso
- Revisa los logs en la consola de la aplicación

