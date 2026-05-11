import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# Configuración del Broker
BROKER = "localhost" 
PORT = 1883
TOPIC_BASE = "seguridad/ciudadana"

# Lista de sensores simulados
SENSORES = [
    {"id": "PIR-001", "tipo": "movimiento", "lat": -18.012, "lon": -70.248},
    {"id": "GPS-PATRULLA-05", "tipo": "gps", "lat": -18.005, "lon": -70.235},
    {"id": "CAM-CENTRO-01", "tipo": "vision_ia", "lat": -18.015, "lon": -70.250}
]

EVENTOS = ["movimiento_sospechoso", "robo_reportado", "patrullaje_rutina", "emergencia_medica"]

client = mqtt.Client()

try:
    client.connect(BROKER, PORT)
    print(f"Conectado al broker en {BROKER}. Enviando 'ruido'...")

    while True:
        # Elegimos un sensor al azar para simular actividad
        sensor = random.choice(SENSORES)
        evento = random.choice(EVENTOS)
        
        # Generar un pequeño desplazamiento en las coordenadas para simular movimiento real
        lat_act = sensor["lat"] + random.uniform(-0.002, 0.002)
        lon_act = sensor["lon"] + random.uniform(-0.002, 0.002)

        # Estructura de datos idéntica a tu caso práctico
        payload = {
            "sensor": sensor["id"],
            "tipo_sensor": sensor["tipo"],
            "evento": evento,
            "lat": round(lat_act, 6),
            "lon": round(lon_act, 6),
            "timestamp": datetime.now().isoformat()
        }

        # Publicar en un tópico específico según el sensor
        topic = f"{TOPIC_BASE}/{sensor['id']}"
        client.publish(topic, json.dumps(payload))
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviado desde {sensor['id']}: {evento}")
        
        # Pausa aleatoria entre 2 y 5 segundos
        time.sleep(random.randint(2, 5))

except KeyboardInterrupt:
    print("\nSimulador detenido.")
    client.disconnect()
except Exception as e:
    print(f"Error: {e}")