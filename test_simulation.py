# pyrefly: ignore [missing-import]
import random
# pyrefly: ignore [missing-import]
import paho.mqtt.publish as publish
import json
import time
import random
import sys
import argparse

MQTT_TOPIC = "unjbg/sensores/movimiento"

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
            opcion = input("Selecciona el destino [1-3]: ").strip()
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
    
    # Datos de ejemplo para las zonas X, Y, Z de Tacna/Localidad (coordenadas base)
    zonas = [
        {"id": "ESP32_01", "zona": "X", "lat": -18.013, "lon": -70.251},
        {"id": "ESP32_02", "zona": "Y", "lat": -18.015, "lon": -70.255},
        {"id": "ESP32_03", "zona": "Z", "lat": -18.010, "lon": -70.248},
    ]

    for _ in range(5):
        nodo = random.choice(zonas)
        # Añadimos un pequeño ruido aleatorio (~ ±100 metros) a las coordenadas base
        ruido_lat = random.uniform(-0.001, 0.001)
        ruido_lon = random.uniform(-0.001, 0.001)
        
        payload = {
            "sensor_id": nodo["id"],
            "zona": nodo["zona"],
            "valor": round(random.uniform(0, 100), 2),
            "latitud": round(nodo["lat"] + ruido_lat, 6),
            "longitud": round(nodo["lon"] + ruido_lon, 6)
        }
        
        try:
            publish.single(MQTT_TOPIC, payload=json.dumps(payload), hostname=broker_host)
            print(f"Enviado: {payload}")
        except Exception as e:
            print(f"Error enviando MQTT a {broker_host}: {e}. ¿Está corriendo Mosquitto?")
        
        time.sleep(2)

if __name__ == "__main__":
    broker_host = obtener_host()
    simular_esp32(broker_host)
