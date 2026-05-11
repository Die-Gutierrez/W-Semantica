# Guía de Configuración: Mosquitto MQTT Broker

Mosquitto es el encargado de recibir los mensajes del ESP32 y distribuirlos a nuestro sistema Python.

## 1. Instalación en Windows
- Descarga el instalador desde [mosquitto.org/download](https://mosquitto.org/download/).
- Ejecuta el instalador `.exe` (usualmente se instala en `C:\Program Files\mosquitto`).

## 2. Ejecución del Servicio
Mosquitto suele instalarse como un servicio automático. Para verificarlo:
1. Presiona `Win + R`, escribe `services.msc` y dale a Enter.
2. Busca el servicio llamado **Mosquitto Broker**.
3. Asegúrate de que el estado sea **"En ejecución"**. Si no lo está, dale clic derecho e **Iniciar**.

## 3. Ejecución Manual (Para ver los mensajes en vivo)
Si quieres ver qué datos están llegando en tiempo real, puedes correrlo manualmente:
1. Abre una terminal (CMD o Git Bash).
2. Entra a la carpeta de instalación: `cd "C:\Program Files\mosquitto"`.
3. Ejecuta:
   ```bash
   ./mosquitto.exe -v
   ```
   *Nota: Si te da error de "Address already in use", es porque el servicio automático ya está corriendo. No te preocupes, eso es bueno.*

## 4. Configuración de Seguridad (Opcional)
Por defecto, Mosquitto 2.0+ solo permite conexiones desde `localhost`. Como todo tu sistema (Python y Fuseki) está en la misma PC, **no necesitas cambiar nada**. 

Si en el futuro quieres conectar un ESP32 físico desde otra red wifi, deberás editar el archivo `mosquitto.conf` agregando:
```text
listener 1883
allow_anonymous true
```
y reiniciar el servicio.
