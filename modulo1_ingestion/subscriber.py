# pyrefly: ignore [missing-import]
import paho.mqtt.client as mqtt
import json
import sys
import os
import time
import datetime

# Añadir el path raíz para importar common y database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
from modulo1_ingestion.database import SessionLocal, SensorData, init_db

# Guardar la última lectura de cada sensor para evitar duplicidad por ráfagas de red o reconexiones
LAST_READINGS = {}  # { sensor_id: {"valor": float, "timestamp": float} }

# Timestamp hardcoded que emite el ESP32 cuando el GPS no tiene señal
TIMESTAMP_GPS_FALLBACK = "2026-07-11T16:40:00.000000"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado al Broker MQTT en {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
        print(f"Suscrito al tópico: {MQTT_TOPIC}")
    else:
        print(f"Error de conexión, código: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Mensaje recibido: {payload}")

        sensor_id = payload.get("sensor_id")
        valor = payload.get("valor")
        
        # Debounce: Si recibimos el mismo valor del mismo sensor en menos de 2.0 segundos, lo descartamos
        ahora = time.time()
        if sensor_id in LAST_READINGS:
            ultima = LAST_READINGS[sensor_id]
            if ultima["valor"] == valor and (ahora - ultima["timestamp"]) < 2.0:
                print(f"Dato duplicado descartado por debouncer para sensor '{sensor_id}' (valor: {valor})")
                return

        # Actualizar la última lectura registrada
        LAST_READINGS[sensor_id] = {"valor": valor, "timestamp": ahora}

        # --- Extracción de coordenadas (formato ESP32 real: sub-objeto "coordenadas") ---
        # Soporta también el formato legacy del simulador (latitud/longitud en raíz)
        coordenadas = payload.get("coordenadas", {})
        latitud = coordenadas.get("latitud") if coordenadas else payload.get("latitud")
        longitud = coordenadas.get("longitud") if coordenadas else payload.get("longitud")

        # Si el GPS no tiene señal, el ESP32 envía 0.0, 0.0 → guardamos None
        if latitud == 0.0 and longitud == 0.0:
            latitud = None
            longitud = None
            print("Advertencia: GPS sin señal (0.0, 0.0) — coordenadas guardadas como None.")

        # --- Parseo del timestamp ISO 8601 del ESP32 ---
        # El ESP32 usa "2026-07-11T16:40:00.000000" como fallback cuando el GPS no tiene señal.
        # En ese caso usamos None para que SQLAlchemy registre la hora real de ingesta (utcnow).
        ts_str = payload.get("timestamp")
        timestamp = None
        if ts_str and ts_str != TIMESTAMP_GPS_FALLBACK:
            try:
                timestamp = datetime.datetime.fromisoformat(ts_str)
            except ValueError:
                print(f"Advertencia: timestamp inválido '{ts_str}', se usará la hora de ingesta.")

        db = SessionLocal()
        nuevo_dato = SensorData(
            sensor_id=sensor_id,
            zona=payload.get("zona"),
            valor=valor,
            timestamp=timestamp,   # None → SQLAlchemy usa default=utcnow
            latitud=latitud,
            longitud=longitud
        )
        db.add(nuevo_dato)
        db.commit()
        db.close()
        print(f"[OK] Dato guardado - sensor: {sensor_id} | valor: {valor} cm | GPS: {'OK' if latitud else 'sin senal'}")
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

def start_subscriber():
    # Inicializar la BD antes de empezar
    init_db()

    # Usar un Client ID fijo para evitar duplicados en reconexiones del Broker
    client = mqtt.Client(client_id="vps_iot_subscriber", clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"No se pudo conectar al Broker: {e}")

if __name__ == "__main__":
    start_subscriber()
