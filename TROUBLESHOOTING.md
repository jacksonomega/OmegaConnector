# Solución al Error 422 - Debugging Guide

## El Problema
Estás recibiendo un error HTTP 422 (Unprocessable Entity) cuando intentas hacer solicitudes desde tu frontend Angular a `/api/chat`.

## Pasos para Diagnosticar y Solucionar

### 1. **Inicia la Aplicación Omega Bridge**
```bash
python main.py
```
Asegúrate de:
- Hacer clic en "Iniciar Servidor" en la interfaz
- Verificar que dice "Estado: En ejecución"
- Confirmar en los logs que el servidor inició en `http://0.0.0.0:5123`

### 2. **Verifica que el servidor esté respondiendo**
Abre un navegador y ve a:
```
http://localhost:5123/api/health-check
```
Deberías ver:
```json
{"status": "online", "service": "Omega Connector"}
```

### 3. **Ejecuta el script de prueba**
```bash
python test_api.py
```
Esto probará diferentes formatos de solicitud y te mostrará exactamente qué funciona y qué no.

### 4. **Revisa los logs en la aplicación**
Cuando hagas una solicitud desde tu frontend, mira la consola de logs en Omega Bridge. Si aparece un error 422, verás:
```
❌ Error 422 - Validación fallida: [detalles del error]
Body recibido: [el JSON que envió tu frontend]
```

## Formato Correcto de la Solicitud

Tu frontend debe enviar una solicitud POST a `http://localhost:5123/api/chat` con este formato:

### Headers Requeridos:
```javascript
{
  'Content-Type': 'application/json'
}
```

### Body (para streaming):
```json
{
  "model": "gemma3:1b",
  "prompt": "Tu pregunta aquí",
  "stream": true
}
```

### Body (sin streaming):
```json
{
  "model": "gemma3:1b", 
  "prompt": "Tu pregunta aquí",
  "stream": false
}
```

## Código de Ejemplo para Angular

### Servicio TypeScript:

```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class OllamaService {
  private apiUrl = 'http://localhost:5123/api';

  constructor(private http: HttpClient) {}

  // Sin streaming
  chat(model: string, prompt: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/chat`, {
      model: model,
      prompt: prompt,
      stream: false
    });
  }

  // Con streaming
  async *chatStream(model: string, prompt: string): AsyncGenerator<string> {
    const response = await fetch(`${this.apiUrl}/chat`, {
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

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body!.getReader();
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
            return;
          }

          try {
            const parsed = JSON.parse(data);
            yield parsed.chunk;
          } catch (e) {
            // Ignorar líneas malformadas
          }
        }
      }
    }
  }

  // Verificar estado del servidor
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health-check`);
  }
}
```

### Uso en un Componente:

```typescript
import { Component } from '@angular/core';
import { OllamaService } from './services/ollama.service';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html'
})
export class ChatComponent {
  response: string = '';
  loading: boolean = false;

  constructor(private ollamaService: OllamaService) {}

  // Sin streaming
  async sendMessage(prompt: string) {
    this.loading = true;
    try {
      const result = await this.ollamaService.chat('gemma3:1b', prompt).toPromise();
      this.response = result.response;
    } catch (error) {
      console.error('Error:', error);
    } finally {
      this.loading = false;
    }
  }

  // Con streaming
  async sendMessageStream(prompt: string) {
    this.loading = true;
    this.response = '';
    
    try {
      for await (const chunk of this.ollamaService.chatStream('gemma3:1b', prompt)) {
        this.response += chunk;
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      this.loading = false;
    }
  }
}
```

## Problemas Comunes y Soluciones

### 1. Error 422 - "Validation Error"
**Causa:** El formato del JSON no es correcto.
**Solución:** Asegúrate de que estás enviando `model` y `prompt` como strings.

### 2. Error CORS
**Causa:** El navegador está bloqueando la solicitud.
**Solución:** El servidor ya está configurado con CORS habilitado para `*`. Si el problema persiste, verifica que estés usando el protocolo correcto (http, no https para localhost).

### 3. Error 500 - "Internal Server Error"
**Causa:** El modelo no está instalado o Ollama no está ejecutándose.
**Solución:** 
- Verifica que Ollama esté corriendo
- Descarga el modelo desde la interfaz de Omega Bridge
- Revisa los logs en la consola de la aplicación

### 4. Timeout o no responde
**Causa:** El modelo está cargando en memoria por primera vez.
**Solución:** La primera solicitud puede tardar más. Espera unos segundos.

## Depuración Avanzada

### Ver exactamente qué está enviando tu frontend:

1. Abre las DevTools del navegador (F12)
2. Ve a la pestaña "Network"
3. Haz la solicitud desde tu frontend
4. Haz clic en la solicitud `/api/chat`
5. Ve a la pestaña "Payload" para ver qué se envió
6. Ve a "Response" para ver el error detallado

### Verificar en Omega Bridge:

Mira la consola de logs en la aplicación. Cada solicitud se registra con:
- Timestamp
- Método y ruta
- Modelo usado
- Primeros 50 caracteres del prompt
- Cualquier error que ocurra

## Contacto y Soporte

Si sigues teniendo problemas:
1. Captura una screenshot de los logs en Omega Bridge
2. Captura el payload completo de la solicitud en DevTools
3. Comparte el mensaje de error exacto

El manejador de errores 422 ahora registra automáticamente el body de la solicitud para ayudar en la depuración.

