# 🚀 Omega Bridge - Gestor de Modelos de Inteligencia Artificial

**Omega Bridge** es una aplicación que te permite gestionar modelos de inteligencia artificial en tu computadora de forma sencilla. Con una interfaz moderna y fácil de usar, puedes descargar, instalar y usar diferentes modelos de IA sin necesidad de conocimientos técnicos.

## ¿Qué hace esta aplicación?

Omega Bridge actúa como un **puente** entre tu computadora y los modelos de inteligencia artificial. Te permite:

- 📥 **Descargar modelos de IA** desde internet
- 🗑️ **Eliminar modelos** que ya no necesites
- 🖥️ **Gestionar modelos** con una interfaz visual
- 🌐 **Crear un servidor local** para que otras aplicaciones puedan usar los modelos
- 📊 **Monitorear el progreso** de las descargas y operaciones

## 🤖 ¿Qué son los Modelos de IA?

Los modelos de inteligencia artificial son como "cerebros digitales" que pueden:
- Responder preguntas
- Escribir textos
- Mantener conversaciones
- Ayudar con tareas de escritura
- Analizar información

Omega Bridge incluye varios modelos con diferentes capacidades:

### Modelos Disponibles

**🔹 Modelos Qwen (Recomendados para principiantes)**
- **Qwen 4B**: Modelo pequeño y rápido (4GB aproximadamente)
- **Qwen 8B**: Modelo equilibrado entre velocidad y calidad (8GB aproximadamente)
- **Qwen 30B**: Modelo grande y potente (30GB aproximadamente)

**🔹 Modelos Gemma (Eficientes)**
- **Gemma 1B**: Muy pequeño y rápido (1GB aproximadamente)
- **Gemma 4B**: Pequeño pero capaz (4GB aproximadamente)
- **Gemma 12B**: Modelo mediano con buena calidad (12GB aproximadamente)
- **Gemma 27B**: Modelo grande y avanzado (27GB aproximadamente)

**🔹 Modelos GPT-OSS (Avanzados)**
- **GPT-OSS 20B**: Modelo muy grande (20GB aproximadamente)
- **GPT-OSS 120B**: Modelo extremadamente grande (120GB aproximadamente)

## 💻 Requisitos de tu Computadora

### Requisitos Mínimos
- **Sistema Operativo**: Windows 10 o superior
- **Memoria RAM**: 8 GB mínimo (16 GB recomendado)
- **Espacio en Disco**: 20 GB libres
- **Conexión a Internet**: Para descargar modelos

### Requisitos por Modelo
- **Modelos pequeños (1B-4B)**: 8 GB de RAM
- **Modelos medianos (8B-12B)**: 16 GB de RAM
- **Modelos grandes (20B+)**: 32 GB de RAM o más

**💡 Recomendación**: Si eres nuevo, comienza con **Qwen 4B** o **Gemma 4B** que funcionan bien en la mayoría de computadoras.

## 🚀 Cómo Usar Omega Bridge

### Paso 1: Abrir la Aplicación
1. Ejecuta el archivo `OmegaBridge.exe` (si tienes el ejecutable)
2. O ejecuta `python main.py` (si tienes el código fuente)
3. Se abrirá una ventana con la interfaz de la aplicación

### Paso 2: Entender la Interfaz

La aplicación tiene **3 secciones principales**:

#### 🎛️ Control del Servidor (Arriba izquierda)
- **Indicador de Estado**: Un círculo que muestra si el servidor está activo
  - 🔴 Rojo = Apagado
  - 🟢 Verde = Funcionando
- **Botón de Control**: Para encender/apagar el servidor
- **URL del Servidor**: Dirección donde otras aplicaciones pueden conectarse

#### 🤖 Gestión de Modelos (Arriba derecha)
- **Lista de Modelos**: Menú para seleccionar qué modelo quieres usar
- **Estado del Modelo**: Te dice si el modelo está instalado o necesita descarga
- **Botón Descargar**: Para descargar el modelo seleccionado
- **Botón Eliminar**: Para borrar modelos que ya no uses
- **Barra de Progreso**: Muestra el avance de las descargas

#### 📋 Consola de Información (Abajo)
- **Registro de Actividad**: Muestra todo lo que está pasando
- **Botón Limpiar**: Para borrar el historial de mensajes

## 📥 Cómo Descargar un Modelo

1. **Selecciona un Modelo**: Haz clic en el menú desplegable y elige un modelo
2. **Verifica el Estado**: Si dice "necesita ser descargado", continúa
3. **Haz Clic en Descargar**: Presiona el botón azul "Descargar"
4. **Espera la Descarga**: 
   - Verás una barra de progreso
   - En la consola aparecerán mensajes de descarga
   - Puede tomar varios minutos dependiendo del tamaño del modelo
5. **Descarga Completa**: Cuando termine, el estado cambiará a "instalado y listo"

## 🗑️ Cómo Eliminar un Modelo

1. **Selecciona el Modelo**: Elige un modelo que ya esté instalado
2. **Haz Clic en Eliminar**: Presiona el botón rojo "Eliminar"
3. **Confirma la Eliminación**: Aparecerá una ventana preguntando si estás seguro
4. **Confirma**: Haz clic en "Eliminar" para confirmar
5. **Modelo Eliminado**: El espacio en disco se liberará

## 🌐 Cómo Iniciar el Servidor

1. **Asegúrate de Tener un Modelo**: Descarga al menos un modelo primero
2. **Haz Clic en "Iniciar Servidor"**: Botón verde en la sección de control
3. **Servidor Activo**: El indicador se pondrá verde y dirá "ONLINE"
4. **Listo para Usar**: Otras aplicaciones ya pueden conectarse al servidor

Para **detener el servidor**:
- Haz clic en "Detener Servidor" (botón rojo)
- El indicador se pondrá rojo y dirá "OFFLINE"

## 📊 Qué Muestra la Consola

La consola de información te muestra en tiempo real:

### Mensajes de Inicio
- `🚀 Aplicación Omega Bridge iniciada`
- `📊 Interfaz moderna cargada correctamente`

### Durante Descargas
- `Descargando qwen3:4b...`
- `pulling manifest`
- `downloading sha256:abc123...`
- `verifying sha256:abc123...`
- `✅ Modelo descargado exitosamente`

### Control del Servidor
- `✅ Servidor FastAPI iniciado en http://0.0.0.0:5123`
- `⏹️ Servidor detenido`

### Errores Comunes
- `❌ Error: No se encuentra ollama`
- `❌ Error al conectar con el servidor`
- `❌ Modelo no encontrado`

### Actividad del Servidor
- `GET /api/health-check - Health check`
- `POST /api/chat - Model: qwen3:4b, Prompt: Hola...`

## 🔧 Consejos y Recomendaciones

### Para Principiantes
1. **Comienza con modelos pequeños** (Qwen 4B o Gemma 4B)
2. **Descarga solo un modelo al principio** para probar
3. **Mantén la aplicación abierta** mientras uses los modelos
4. **Revisa la consola** si algo no funciona

### Gestión de Espacio
- **Elimina modelos que no uses** para liberar espacio
- **Los modelos grandes pueden ocupar muchos GB**
- **Puedes tener varios modelos instalados** al mismo tiempo

### Rendimiento
- **Modelos más grandes = mejor calidad pero más lento**
- **Modelos más pequeños = más rápido pero menos capaz**
- **Cierra otros programas pesados** al usar modelos grandes

## ❓ Problemas Comunes

### "No se encuentra ollama"
- **Problema**: Falta instalar Ollama
- **Solución**: Descarga e instala Ollama desde https://ollama.ai/download

### "Error al iniciar servidor"
- **Problema**: Puerto ocupado o permisos
- **Solución**: Reinicia la aplicación o tu computadora

### "Descarga muy lenta"
- **Problema**: Conexión lenta a internet
- **Solución**: Ten paciencia, los modelos son archivos grandes

### "No tengo suficiente RAM"
- **Problema**: Modelo muy grande para tu computadora
- **Solución**: Usa un modelo más pequeño (1B o 4B)

## 🎯 Flujo de Trabajo Recomendado

1. **Primera Vez**:
   - Abre la aplicación
   - Selecciona "Qwen 4B" o "Gemma 4B"
   - Descarga el modelo
   - Inicia el servidor

2. **Uso Regular**:
   - Abre la aplicación
   - Inicia el servidor
   - Usa tu aplicación web favorita que se conecte al servidor

3. **Mantenimiento**:
   - Elimina modelos que no uses
   - Prueba modelos nuevos según tus necesidades
   - Revisa la consola si hay problemas

---

**¡Disfruta usando Omega Bridge!** 🎉

*Si necesitas ayuda adicional, revisa los mensajes en la consola de la aplicación para obtener más información sobre lo que está sucediendo.*
