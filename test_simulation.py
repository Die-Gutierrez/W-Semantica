# pyrefly: ignore [missing-import]
import random
# pyrefly: ignore [missing-import]
import paho.mqtt.publish as publish
import json
import time
import sys
import argparse
import datetime
from datetime import timezone

MQTT_TOPIC = "unjbg/sensores/movimiento"

# URI semántica fija que usa el ESP32 real
OBSERVACION_URI = "http://example.org/unjbg/observation/1"

def obtener_host():
    parser = argparse.ArgumentParser(description="Simulador de sensores ESP32 (MQTT)")
    parser.add_argument(
        "--host", 
        type=str, 
        help="Dirección IP o dominio del Broker MQTT (ej: localhost, 95.111.236.12)"
    )
    args, unknown = parser.parse_known_args()

    if args.host:
        return args.host

    # Si no se pasó argumento, mostrar menú interactivo
    print("==================================================")
    print("   Simulador de Sensores IoT - Selección de Host   ")
    print("==================================================")
    print("1. Local (localhost / 127.0.0.1)")
    print("2. VPS de Pruebas (95.111.236.12)")
    print("==================================================")
    
    while True:
        try:
            opcion = input("Selecciona el destino [1-2]: ").strip()
            if opcion == "1":
                return "localhost"
            elif opcion == "2":
                return "95.111.236.12"
            else:
                print("Opción no válida. Ingrese 1 o 2.")
        except KeyboardInterrupt:
            print("\nSimulación cancelada.")
            sys.exit(0)

def simular_esp32(broker_host):
    print(f"Iniciando simulación de ESP32 enviando datos a {broker_host}...")
    print("Formato: ESP32 real (coordenadas anidadas + timestamp ISO 8601)")
    
    # Datos de ejemplo para las zonas de Tacna/Localidad (coordenadas base)
    zonas = [
        {"id": "ESP32 01", "zona": "A fredy",   "lat": -18.013, "lon": -70.251},
        {"id": "ESP32 02", "zona": "B fredef",  "lat": -18.015, "lon": -70.255},
        {"id": "ESP32 03", "zona": "C daniel",  "lat": -18.010, "lon": -70.248},
    ]

    for i in range(5):
        nodo = random.choice(zonas)
        # Añadimos un pequeño ruido aleatorio (~ ±100 metros) a las coordenadas base
        ruido_lat = random.uniform(-0.001, 0.001)
        ruido_lon = random.uniform(-0.001, 0.001)

        # Timestamp actual en formato ISO 8601 (igual que el GPS del ESP32)
        ts_now = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000")

        # Payload con la estructura exacta del ESP32 real
        payload = {
            "observacion": OBSERVACION_URI,
            "sensor_id": nodo["id"],
            "valor": round(random.uniform(0, 400), 2),  # Distancia en cm (rango realista del HC-SR04)
            "timestamp": ts_now,
            "zona": nodo["zona"],
            "coordenadas": {
                "latitud": round(nodo["lat"] + ruido_lat, 6),
                "longitud": round(nodo["lon"] + ruido_lon, 6)
            }
        }
        
        try:
            publish.single(MQTT_TOPIC, payload=json.dumps(payload), hostname=broker_host)
            print(f"[{i+1}/5] Enviado -> sensor: {payload['sensor_id']} | valor: {payload['valor']} cm | zona: {payload['zona']}")
        except Exception as e:
            print(f"Error enviando MQTT a {broker_host}: {e}. ¿Está corriendo Mosquitto?")
        
        time.sleep(2)

    print("\n[OK] Simulacion completada.")

if __name__ == "__main__":
    broker_host = obtener_host()
    simular_esp32(broker_host)

