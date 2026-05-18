# Proyecto Web Semántica - IoT Geoespacial (UNJBG 2026)

Este proyecto implementa un flujo completo de datos IoT: desde la captura mediante sensores (ESP32) hasta la exposición semántica a través de una API GeoJSON.

## 🚀 Guía de Ejecución Rápida

## 📦 Carpeta de Requisitos

Dentro de la carpeta `/requisitos` encontrarás:

- `requirements.txt`: El listado técnico de librerías.
- `explicacion.md`: Un detalle pedagógico de para qué sirve cada librería en este proyecto semántico.

En la carpeta tambien se encuentran los requisitos de software del proyecto:

- [Python 3.12.6](https://www.python.org/downloads/release/python-3126/)
- mosquito-2.1.2
- fuseki-4.6.0-distribution.zip
- OpenJDK21

### 1. Configuración del Entorno Virtual (Recomendado)

Para mantener las dependencias del proyecto aisladas, es recomendable crear un entorno virtual:

**En Windows (PowerShell / Command Prompt):**

```powershell
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno
.venv\Scripts\activate
```

**En Windows (Git Bash):**

```bash
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno
source .venv/Scripts/activate
```

### 2. Instalación de Dependencias

Una vez activado el entorno virtual, instala las librerías necesarias:

```bash
pip install -r requisitos/requirements.txt
```

### 3. Servicios Base

Asegúrate de tener iniciados:

1. **Mosquitto** (Broker MQTT) en el puerto 1883.
2. **Apache Jena Fuseki** en el puerto 3030.
   - Crea un dataset llamado `iot_sensores`.

---

## 🛠️ Flujo de los 3 Módulos

Para que el sistema funcione, debes seguir este orden:

### Paso 1: Ingesta y Almacenamiento (Módulo 1)

Este script actúa como el "puente" entre el mundo físico (sensores) y el mundo digital.

- **¿Qué hace?**: Se conecta al Broker MQTT y se queda escuchando permanentemente. Cada vez que el ESP32 envía un mensaje con datos de movimiento, este script lo captura, lo valida y lo inserta en una base de datos relacional.
- **Tecnologías**: `paho-mqtt` para la comunicación y `SQLAlchemy` para el manejo de la base de datos SQLite.

```bash
python modulo1_ingestion/subscriber.py
```

**Resultado**: Los datos quedan persistidos en el archivo `iot_data.db`. Sin este paso, los datos de los sensores se perderían tras ser enviados.

### Paso 2: Simulación de Sensores (Pruebas)

Como no siempre tenemos el hardware conectado, este script emula el comportamiento de varios sensores ESP32 distribuidos en diferentes zonas.

- **¿Qué hace?**: Genera datos aleatorios de movimiento y coordenadas geográficas (latitud/longitud) de Tacna, enviándolos a través del protocolo MQTT al tópico configurado.

```bash
python test_simulation.py
```

### Paso 3: Transformación Semántica (Módulo 2) - EL NÚCLEO

Este es el paso más importante de la asignatura. Aquí los datos dejan de ser simples filas en una tabla y se convierten en **conocimiento**.

- **¿Qué hace?**: Toma cada registro de SQLite y lo traduce al lenguaje de la Web Semántica (RDF). Utiliza la ontología **SOSA** para describir la observación del sensor y **GeoSPARQL** para describir su ubicación exacta en el mapa. Una vez creado este "grafo", lo sube al Triplestore (Fuseki).
- **Tecnologías**: `rdflib` para la creación del grafo y peticiones `HTTP/SPARQL` para la carga en Fuseki.

```bash
python modulo2_semantica/etl_mapper.py
```

**Resultado**: Tus datos ahora son consultables mediante **SPARQL** y están listos para enlazarse con otras fuentes de datos (Linked Data).

### Paso 4: API de Servicio Geoespacial (Módulo 3)

Este módulo es el que conecta tus datos semánticos con las aplicaciones del mundo real (como un mapa web).

- **¿Qué hace?**: Expone un servicio web que, al recibir una petición, realiza una consulta SPARQL interna a Fuseki para extraer la ubicación y los valores de los sensores. Convierte esa respuesta compleja de grafos a un formato **GeoJSON**, que es el estándar que entienden los mapas modernos.
- **Tecnologías**: `FastAPI` para el servidor web y `requests` para consultar a Fuseki.

```bash
python modulo3_api/main.py
```

**Acceso**: Abre `http://localhost:8000/api/v1/sensors/geojson` en tu navegador para ver los datos listos para el mapa.

---

## 📂 ¿Dónde se guardan los datos?

1. **Datos Crudos**: En el archivo `iot_data.db` (Base de Datos Relacional SQLite).
2. **Datos Semánticos**: Dentro de **Apache Jena Fuseki** (Base de Datos de Grafos / Triplestore).

---

_Desarrollado para la asignatura de Web Semántica - UNJBG._
