# pyrefly: ignore [missing-import]
import paho.mqtt.client as mqtt
import json
import sys
import os

# Añadir el path raíz para importar common y database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
from modulo1_ingestion.database import SessionLocal, SensorData, init_db

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

        db = SessionLocal()
        nuevo_dato = SensorData(
            sensor_id=payload.get("sensor_id"),
            zona=payload.get("zona"),
            valor=payload.get("valor"),
            latitud=payload.get("latitud"),
            longitud=payload.get("longitud")
        )
        db.add(nuevo_dato)
        db.commit()
        db.close()
        print("Dato guardado en la base de datos.")
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

def start_subscriber():
    # Inicializar la BD antes de empezar
    init_db()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"No se pudo conectar al Broker: {e}")

if __name__ == "__main__":
    start_subscriber()
