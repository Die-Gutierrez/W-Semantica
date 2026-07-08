# Guía de Despliegue en VPS (Ubuntu 24.04 LTS) - Rol de Root

Esta guía está diseñada específicamente para desplegar tu proyecto en un VPS Ubuntu 24.04 limpio utilizando la cuenta de administrador **`root`**. Por tanto, la ubicación del proyecto en el servidor será de forma fija: `/root/W-Semantica`.

---

## 🗂️ Resumen de la Arquitectura en Producción

En lugar de iniciar manualmente los scripts usando `run_all.py` (lo cual es genial para desarrollo local), en el servidor de producción utilizaremos **systemd** de Linux. Esto garantiza que todos tus servicios:
1. Se ejecuten en segundo plano sin bloquear tu terminal.
2. Se inicien automáticamente si el servidor VPS se reinicia.
3. Se reinicien automáticamente si sufren algún fallo.

Hay **4 servicios en total** corriendo en segundo plano:
* **`fuseki.service`**: El motor del Triplestore (Apache Jena Fuseki) en el puerto `3030`.
* **`iot-subscriber.service`** (Módulo 1): El receptor de datos MQTT que graba en SQLite.
* **`iot-etl.service`** (Módulo 2): El cargador semántico incremental que sube RDF a Fuseki.
* **`iot-api.service`** (Módulo 3): La API FastAPI en el puerto `8000` con Swagger integrado.

---

## 🛠️ Fase 1: Conexión y Preparación del Sistema

### 1. Conectarse al VPS por SSH
Abre la consola de tu computadora local y ejecuta:
```bash
ssh root@ip_de_tu_vps
```
*(Reemplaza `ip_de_tu_vps` por la IP pública de tu servidor).*

### 2. Actualizar el Servidor
Una vez dentro como root, actualiza el sistema:
```bash
apt update && apt upgrade -y
```

### 3. Instalar Herramientas Básicas y Git
Instala utilidades necesarias para la automatización:
```bash
apt install -y git curl unzip ufw python3-pip python3-venv python3-full
```

---

## 📦 Fase 2: Instalación de Dependencias del Sistema

### 1. Verificar Java 21 (Requerido por Fuseki)
Dado que ya verificaste que tienes instalado Java 21, no es necesario instalarlo:
```bash
# Ya activo en tu sistema:
openjdk version "21.0.11" 2026-04-21
```

### 2. Instalar Mosquitto (Broker MQTT)
Instala el broker de mensajería:
```bash
apt install -y mosquitto mosquitto-clients
```

---

## 📡 Fase 3: Configurar Mosquitto para Sensores Físicos Reales

> [!WARNING]
> Por defecto en Mosquitto 2.0+, el broker solo acepta conexiones locales (`localhost`) y rechaza conexiones externas. Para recibir datos de un **sensor físico real** (como un ESP32 en tu red local) que transmite a través de Internet al VPS, debemos configurar Mosquitto para escuchar en la interfaz de red pública y permitir el acceso.

Existen dos opciones para configurar esto: **Opción A (Rápida y Abierta)** o **Opción B (Segura con Usuario y Contraseña)**.

### Opción A: Configuración Abierta (Solo para Pruebas Rápidas)
Esta opción permite que cualquier dispositivo en Internet se conecte al broker sin contraseña.

1. Crea o edita el archivo de configuración adicional de Mosquitto:
   ```bash
   nano /etc/mosquitto/conf.d/external.conf
   ```
2. Agrega las siguientes líneas:
   ```ini
   # Escuchar en todas las interfaces de red en el puerto 1883
   listener 1883 0.0.0.0
   # Permitir conexiones sin usuario/contraseña
   allow_anonymous true
   ```
3. Guarda (`Ctrl + O`, `Enter`) y sal (`Ctrl + X`).
4. Reinicia Mosquitto para aplicar los cambios:
   ```bash
   systemctl restart mosquitto
   ```

---

### Opción B: Configuración Segura con Usuario y Contraseña (Recomendada)
Para evitar que personas ajenas publiquen datos falsos en tu servidor, es mejor configurar credenciales.

1. Crea un usuario MQTT (por ejemplo, `sensor_esp32`):
   ```bash
   mosquitto_passwd -c /etc/mosquitto/passwd sensor_esp32
   ```
   *Te pedirá ingresar y confirmar una contraseña. Memorízala para la programación de tu ESP32.*

2. Crea o edita el archivo de configuración:
   ```bash
   nano /etc/mosquitto/conf.d/external.conf
   ```
3. Agrega las siguientes líneas:
   ```ini
   # Escuchar en todas las interfaces de red en el puerto 1883
   listener 1883 0.0.0.0
   # Desactivar accesos anónimos
   allow_anonymous false
   # Ruta al archivo de contraseñas
   password_file /etc/mosquitto/passwd
   ```
4. Guarda (`Ctrl + O`, `Enter`) y sal (`Ctrl + X`).
5. Reinicia Mosquitto:
   ```bash
   systemctl restart mosquitto
   ```

---

### 4. Abrir el puerto 1883 en el Firewall del VPS
Debes permitir que el tráfico MQTT entre a tu servidor. Si usas el firewall UFW, ejecuta:
```bash
ufw allow 1883/tcp
```

---

## 🔄 Fase 4: Configurar Despliegue Automático (CI/CD con GitHub Actions)

Para evitar usar los servidores de GitHub para compilar y mantener el proceso liviano, configuraremos una acción de SSH. Cuando hagas `git push origin main` desde tu computadora local:
1. GitHub Actions se conectará a tu VPS usando SSH como `root` de manera segura.
2. Descargará los últimos cambios con `git pull` directamente en `/root/W-Semantica`.
3. Actualizará las dependencias en el entorno virtual si es necesario.
4. Reiniciará los servicios de systemd para que los cambios surtan efecto de inmediato.

### 1. Crear Llaves SSH para GitHub Actions en el VPS (como root)
Para que GitHub se conecte a tu VPS sin contraseña:
1. En la consola de tu VPS (en la sesión de root), genera un nuevo par de llaves:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/github_deploy_key -N ""
   ```
2. Agrega la llave pública a la lista de llaves autorizadas de root:
   ```bash
   cat ~/.ssh/github_deploy_key.pub >> ~/.ssh/authorized_keys
   ```
3. Obtén la llave privada para agregarla a GitHub:
   ```bash
   cat ~/.ssh/github_deploy_key
   ```
   *Copia todo el contenido de la llave que empieza con `-----BEGIN OPENSSH PRIVATE KEY-----` hasta `-----END OPENSSH PRIVATE KEY-----`.*

---

### 2. Configurar Secrets en GitHub
Ve a tu repositorio en la página web de GitHub:
1. Ve a **Settings** -> **Secrets and variables** -> **Actions**.
2. Haz clic en **New repository secret** y agrega los siguientes secretos:
   - `VPS_HOST`: La IP pública de tu VPS.
   - `VPS_USER`: `root`
   - `VPS_SSH_KEY`: Pega la llave privada que copiaste en el paso anterior.
   - `VPS_PORT`: `22` (o el puerto SSH personalizado si lo cambiaste).

*Nota: Dado que te estás conectando directamente como `root`, no necesitas hacer ninguna configuración de permisos `sudo` ni `sudoers`.*

---

### 3. Flujo de Trabajo en GitHub (Ya creado localmente)
Hemos creado el archivo del workflow en tu repositorio local en la ruta `.github/workflows/deploy.yml`. El contenido completo es:
```yaml
name: Deploy to VPS

on:
  push:
    branches:
      - main

jobs:
  deploy:
    name: Deploy Application
    runs-on: ubuntu-latest
    steps:
      - name: SSH and Deploy
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          port: ${{ secrets.VPS_PORT || 22 }}
          script: |
            cd /root/W-Semantica
            # Traer los últimos cambios descartando cualquier cambio local si existiera
            git fetch --all
            git reset --hard origin/main
            # Actualizar dependencias de python si hay cambios
            source .venv/bin/activate
            pip install -r requirements.txt
            # Reiniciar servicios para cargar los cambios de código
            systemctl restart iot-subscriber.service iot-etl.service iot-api.service
            # Mostrar estado para verificar que todo levantó correctamente
            systemctl status iot-subscriber.service iot-etl.service iot-api.service --no-pager
```

---

## 📁 Fase 5: Clonar el Proyecto y Configurar Python

### 1. Clonar el Repositorio en el Servidor (en /root)
Nos ubicaremos en la carpeta del usuario root y clonaremos tu proyecto:
```bash
cd /root
git clone https://github.com/Die-Gutierrez/W-Semantica.git
cd W-Semantica
```

### 2. Crear y Activar el Entorno Virtual de Python
Dentro de la carpeta del proyecto:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias de Python
Instalamos todas las librerías necesarias especificadas en tus requerimientos:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🏛️ Fase 6: Instalación y Configuración de Apache Jena Fuseki

### 1. Descargar y Descomprimir Fuseki
```bash
# Volver a una carpeta temporal para descargar
cd /tmp
# Descargamos Apache Jena Fuseki (versión 4.9.0)
wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-4.9.0.tar.gz

# Extraer en /opt
tar -zxvf apache-jena-fuseki-4.9.0.tar.gz -C /opt
mv /opt/apache-jena-fuseki-4.9.0 /opt/fuseki
```

### 2. Configurar Fuseki como Servicio de Systemd
Para que Fuseki se ejecute en segundo plano:
```bash
nano /etc/systemd/system/fuseki.service
```

Pega el siguiente contenido:
```ini
[Unit]
Description=Apache Jena Fuseki Triplestore
After=network.target

[Service]
Type=simple
Environment=FUSEKI_HOME=/opt/fuseki
WorkingDirectory=/opt/fuseki
ExecStart=/usr/bin/java -Xmx2g -jar /opt/fuseki/fuseki-server.jar
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Iniciar el Servicio de Fuseki
```bash
systemctl daemon-reload
systemctl enable fuseki
systemctl start fuseki
```

### 4. Crear el Dataset en Fuseki
Fuseki ahora está corriendo localmente en el puerto `3030`. Crea el dataset `iot_sensores`:
```bash
curl -u admin:admin -X POST http://localhost:3030/$/datasets \
  --data "dbName=iot_sensores" \
  --data "dbType=tdb2"
```

---

## ⚡ Fase 7: Configurar los Módulos del Proyecto como Servicios

Crearemos servicios del sistema para los 3 módulos del proyecto. Al estar usando root, todas las rutas de trabajo y el ejecutable del entorno virtual apuntarán exactamente a `/root/W-Semantica`.

### 1. Servicio para el Suscriptor MQTT (Módulo 1)
```bash
nano /etc/systemd/system/iot-subscriber.service
```
Pega lo siguiente:
```ini
[Unit]
Description=IoT MQTT Subscriber (Modulo 1)
After=network.target mosquitto.service

[Service]
Type=simple
WorkingDirectory=/root/W-Semantica
ExecStart=/root/W-Semantica/.venv/bin/python -u modulo1_ingestion/subscriber.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Servicio para el ETL Mapper Semántico (Módulo 2)
```bash
nano /etc/systemd/system/iot-etl.service
```
Pega lo siguiente:
```ini
[Unit]
Description=IoT ETL Mapper Semantico (Modulo 2)
After=network.target fuseki.service

[Service]
Type=simple
WorkingDirectory=/root/W-Semantica
ExecStart=/root/W-Semantica/.venv/bin/python -u modulo2_semantica/etl_mapper.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 3. Servicio para la API GeoJSON (Módulo 3)
```bash
nano /etc/systemd/system/iot-api.service
```
Pega lo siguiente:
```ini
[Unit]
Description=IoT FastAPI Service (Modulo 3)
After=network.target fuseki.service

[Service]
Type=simple
WorkingDirectory=/root/W-Semantica
ExecStart=/root/W-Semantica/.venv/bin/python -u -m uvicorn modulo3_api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## 🚀 Fase 8: Activar y Probar Todo el Sistema

### 1. Cargar e Iniciar todos los Servicios
```bash
systemctl daemon-reload

# Habilitar servicios para que arranquen en el inicio del VPS
systemctl enable iot-subscriber
systemctl enable iot-etl
systemctl enable iot-api

# Iniciar los servicios
systemctl start iot-subscriber
systemctl start iot-etl
systemctl start iot-api
```

### 2. Verificar el Estado de cada Servicio
```bash
systemctl status iot-subscriber
systemctl status iot-etl
systemctl status iot-api
```

---

## 🔌 Fase 9: Transición de Pruebas a Sensores Físicos Reales

### 1. ¿Cómo apagar el "Mosquitto Virtual de Pruebas"?
El script `test_simulation.py` (nuestro simulador virtual) **no corre en segundo plano como un servicio**. Es un script interactivo.
- Si lo ejecutaste en la terminal con `python test_simulation.py`, simplemente presiona `Ctrl + C` en esa terminal para detenerlo.
- El suscriptor (`iot-subscriber.service`) seguirá corriendo en segundo plano esperando mensajes de cualquier origen (virtual o real).

### 2. Configurar el Sensor Físico Real (ESP32)
Para enviar datos desde tu placa física (ESP32, ESP8266, Raspberry Pi, etc.) hacia tu VPS:

1. **Configuración de Conexión en el Código de tu ESP32:**
   - **Broker IP**: La IP pública de tu VPS (ej. `190.120.85.22` o tu dominio).
   - **Port**: `1883`.
   - **Topic**: `unjbg/sensores/movimiento` (o cualquier tópico que encaje con el patrón `unjbg/sensores/#` que escucha el suscriptor).
   - **Credenciales** (si configuraste la *Opción B* de Mosquitto):
     - Usuario: `sensor_esp32`
     - Contraseña: La que asignaste en el paso `mosquitto_passwd`.

2. **Formato JSON esperado por el Suscriptor:**
   El código en `subscriber.py` deserializa un JSON con la siguiente estructura. Asegúrate de que el payload que envíe tu ESP32 tenga este formato:
   ```json
   {
     "sensor_id": "ESP32_FISICO_01",
     "zona": "X",
     "valor": 45.2,
     "latitud": -18.013,
     "longitud": -70.251
   }
   ```

### 3. Verificar la llegada de datos del Sensor Físico
Para validar que el VPS está recibiendo los datos del ESP32 real, ejecuta el siguiente comando en tu VPS:
```bash
# Ver en vivo los datos que entran a la base de datos a través del suscriptor
journalctl -u iot-subscriber.service -f -n 20
```

Si todo está correcto, verás líneas de log como:
```text
Mensaje recibido: {'sensor_id': 'ESP32_FISICO_01', 'zona': 'X', 'valor': 45.2, ...}
Dato guardado en la base de datos.
```

---

## 📊 Fase 10: Monitoreo y Administración de Consolas de Servicios

Dado que los servicios se ejecutan de manera asíncrona y en segundo plano usando `systemd`, no verás una terminal abierta para cada uno. Todo lo que imprimen mediante `print()`, logs o errores es interceptado por el diario del sistema (`journald`).

### 1. Ver la Consola de Logs en Tiempo Real (Modo Monitoreo)
El flag `-f` (follow) te permite "engancharte" a la terminal de salida del módulo y ver qué está pasando conforme ocurren los eventos.

*   **Consola de la Ingestión MQTT (Módulo 1)**:
    ```bash
    journalctl -u iot-subscriber.service -f
    ```
*   **Consola del ETL Semántico (Módulo 2)**:
    ```bash
    journalctl -u iot-etl.service -f
    ```
*   **Consola de la API FastAPI y Swagger (Módulo 3)**:
    ```bash
    journalctl -u iot-api.service -f
    ```
*   **Consola del Triplestore Fuseki**:
    ```bash
    journalctl -u fuseki.service -f
    ```
*(Para salir de cualquiera de estas vistas y volver a la terminal de comandos de root, presiona **`Ctrl + C`**).*

### 2. Comandos de Consola Avanzados para logs
*   **Ver las últimas 100 líneas del log de un servicio sin quedar bloqueado**:
    ```bash
    journalctl -u iot-subscriber.service -n 100 --no-pager
    ```
*   **Buscar errores críticos de ejecución en la API**:
    ```bash
    journalctl -u iot-api.service -p err
    ```
*   **Ver lo ocurrido durante las últimas 3 horas**:
    ```bash
    journalctl -u iot-etl.service --since "3 hours ago"
    ```

---

## ❓ Preguntas Frecuentes (FAQ)

### ¿Cómo sé si mi proyecto ya tiene Swagger configurado?
**¡Ya está configurado!** FastAPI autogenera de forma interactiva la documentación de Swagger. Una vez que tu API esté activa en el VPS, puedes ingresar a:
`http://TU_IP_VPS:8000/docs`
Allí verás el panel interactivo de Swagger UI para probar los endpoints en vivo.

### ¿Puedo recibir datos de múltiples sensores físicos distintos en este VPS?
**Sí, el sistema es multitenant nativo.**
* Mosquitto escucha en `0.0.0.0:1883`, aceptando cualquier dispositivo.
* El tópico que escucha tu suscriptor usa el wildcard `#` (`unjbg/sensores/#`), por lo que recibirá cualquier sub-tópico.
* La base de datos guarda automáticamente el `sensor_id` que el dispositivo envía en su payload JSON, lo que permite diferenciar lecturas de distintos dispositivos sin cambios en el código.

### ¿Cómo detengo de forma temporal o reinicio un servicio manualmente?
Como root, puedes usar la herramienta `systemctl` con los siguientes comandos (ejemplo con la API):
*   **Detener**: `systemctl stop iot-api`
*   **Iniciar**: `systemctl start iot-api`
*   **Reiniciar**: `systemctl restart iot-api`

### ¿Qué pasa si el servidor VPS se apaga o se reinicia accidentalmente?
Gracias a la directiva `WantedBy=multi-user.target` en nuestros archivos de servicio systemd y a que ejecutamos `systemctl enable <nombre>`, el sistema operativo Ubuntu se encargará de levantar automáticamente Mosquitto, Fuseki, el Suscriptor MQTT, el ETL y la API FastAPI en el orden correcto apenas se inicie el sistema, garantizando disponibilidad 24/7 sin intervención manual.

### ¿Dónde puedo ver la base de datos relacional y dónde la semántica?
1. **SQLite (`iot_data.db`)**: Es un archivo de base de datos local guardado en `/root/W-Semantica/iot_data.db`.
2. **Triplestore Fuseki**: Guarda los datos semánticos indexados en su base interna TDB2 dentro del servidor. Puedes consultarlos ejecutando peticiones SPARQL a `http://localhost:3030/iot_sensores/query`.
