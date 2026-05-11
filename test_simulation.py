# pyrefly: ignore [missing-import]
import paho.mqtt.publish as publish
import json
import time
import random

MQTT_BROKER = "localhost"
MQTT_TOPIC = "unjbg/sensores/movimiento"

def simular_esp32():
    print(f"Simulando ESP32 enviando datos a {MQTT_BROKER}...")
    
    # Datos de ejemplo para las zonas X, Y, Z de Tacna/Localidad
    zonas = [
        {"id": "ESP32_01", "zona": "X", "lat": -18.013, "lon": -70.251},
        {"id": "ESP32_02", "zona": "Y", "lat": -18.015, "lon": -70.255},
        {"id": "ESP32_03", "zona": "Z", "lat": -18.010, "lon": -70.248},
    ]

    for _ in range(5):
        nodo = random.choice(zonas)
        payload = {
            "sensor_id": nodo["id"],
            "zona": nodo["zona"],
            "valor": round(random.uniform(0, 100), 2),
            "latitud": nodo["lat"],
            "longitud": nodo["lon"]
        }
        
        try:
            publish.single(MQTT_TOPIC, payload=json.dumps(payload), hostname=MQTT_BROKER)
            print(f"Enviado: {payload}")
        except Exception as e:
            print(f"Error enviando MQTT: {e}. ¿Está corriendo Mosquitto?")
        
        time.sleep(2)

if __name__ == "__main__":
    simular_esp32()
