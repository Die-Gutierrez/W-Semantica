import os
from pathlib import Path

# Rutas Base
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.path.join(BASE_DIR, "iot_data.db")

# Configuración MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "unjbg/sensores/#"

# Configuración SQLite
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Configuración Fuseki
FUSEKI_BASE_URL = "http://localhost:3030"
FUSEKI_DATASET = "iot_sensores"
FUSEKI_UPDATE_URL = f"{FUSEKI_BASE_URL}/{FUSEKI_DATASET}/update"
FUSEKI_QUERY_URL = f"{FUSEKI_BASE_URL}/{FUSEKI_DATASET}/query"

# Configuración de Ontologías (Namespaces)
SOSA = "http://www.w3.org/ns/sosa/"
GEO = "http://www.opengis.net/ont/geosparql#"
EX = "http://example.org/unjbg/"
