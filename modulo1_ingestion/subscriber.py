# pyrefly: ignore [missing-import]
import paho.mqtt.client as mqtt
import json
import sys
import os
import time

# Añadir el path raíz para importar common y database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
from modulo1_ingestion.database import SessionLocal, SensorData, init_db

# Guardar la última lectura de cada sensor para evitar duplicidad por ráfagas de red o reconexiones
LAST_READINGS = {}  # { sensor_id: {"valor": float, "timestamp": float} }

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

        db = SessionLocal()
        nuevo_dato = SensorData(
            sensor_id=sensor_id,
            zona=payload.get("zona"),
            valor=valor,
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

