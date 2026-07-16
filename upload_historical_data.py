# pyrefly: ignore [missing-import]
import csv
import io
import json
import time
import sys
import os
import argparse
import datetime
from datetime import timezone
# pyrefly: ignore [missing-import]
import paho.mqtt.client as mqtt

# Importar configuración MQTT de ser posible
try:
    from common.config import MQTT_TOPIC as CONFIG_MQTT_TOPIC, MQTT_PORT
    MQTT_TOPIC = CONFIG_MQTT_TOPIC.replace("/#", "/movimiento")
except ImportError:
    MQTT_TOPIC = "unjbg/sensores/movimiento"
    MQTT_PORT = 1883

OBSERVACION_BASE_URI = "http://example.org/unjbg/observation"

def parse_latitude(val):
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    if '.' in val_str:
        return float(val_str)
        
    is_negative = val_str.startswith('-')
    digits = ''.join(c for c in val_str if c.isdigit())
    if not digits:
        return None
        
    # Si empieza con '1', asumimos que es una latitud de 2 dígitos (ej. -10 a -19 en Perú)
    # De lo contrario, es de 1 dígito (ej. -5, -6, -9)
    if digits.startswith('1'):
        num_integer_digits = 2
    else:
        num_integer_digits = 1
        
    f_val = float(digits[:num_integer_digits] + '.' + digits[num_integer_digits:])
    return -f_val if is_negative else f_val

def parse_longitude(val):
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    if '.' in val_str:
        return float(val_str)
        
    is_negative = val_str.startswith('-')
    digits = ''.join(c for c in val_str if c.isdigit())
    if not digits:
        return None
        
    # Las longitudes en Perú siempre tienen 2 dígitos enteros (ej. -70s a -80s)
    f_val = float(digits[:2] + '.' + digits[2:])
    return -f_val if is_negative else f_val

def parse_csv_file(csv_path):
    records = []
    if not os.path.exists(csv_path):
        print(f"Error: No se encontró el archivo CSV en la ruta: {csv_path}")
        return []
        
    print(f"Leyendo y parseando el archivo CSV...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Ignorar la cabecera
        f.readline()
        
        for index, raw_line in enumerate(f, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            
            # Limpiar comillas externas y dobles comillas dobles
            if raw_line.startswith('"') and raw_line.endswith('"'):
                cleaned_line = raw_line[1:-1].replace('""', '"')
            else:
                cleaned_line = raw_line.replace('""', '"')
                
            reader = csv.reader(io.StringIO(cleaned_line))
            try:
                row = next(reader)
            except StopIteration:
                continue
                
            if len(row) < 5:
                continue
                
            nombre_sensor = row[0]
            zona = row[1]
            
            try:
                valor = float(row[2])
            except ValueError:
                continue
                
            latitud = parse_latitude(row[3])
            longitud = parse_longitude(row[4])
            
            records.append({
                "sensor_id": nombre_sensor,
                "zona": zona,
                "valor": valor,
                "latitud": latitud,
                "longitud": longitud
            })
            
    print(f"Se cargaron exitosamente {len(records)} registros desde el CSV.")
    return records

def obtener_host():
    parser = argparse.ArgumentParser(description="Subidor de datos históricos vía MQTT")
    parser.add_argument(
        "--host", 
        type=str, 
        help="Dirección IP o dominio del Broker MQTT (ej: localhost, 95.111.236.12)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="dataExterna/DatosHistoricosFiltroII - Hoja 1.csv",
        help="Ruta alternativa al archivo CSV"
    )
    args, unknown = parser.parse_known_args()

    if args.host:
        return args.host, args.csv

    # Mostrar menú interactivo
    print("==================================================")
    print("   Subidor de Históricos - Selección de Broker    ")
    print("==================================================")
    print("1. Local (localhost / 127.0.0.1)")
    print("2. VPS de Pruebas (95.111.236.12)")
    print("==================================================")
    
    while True:
        try:
            opcion = input("Selecciona el destino [1-2]: ").strip()
            if opcion == "1":
                return "localhost", args.csv
            elif opcion == "2":
                return "95.111.236.12", args.csv
            else:
                print("Opción no válida. Ingrese 1 o 2.")
        except KeyboardInterrupt:
            print("\nOperación cancelada.")
            sys.exit(0)

def publicar_historicos(records, broker_host):
    print(f"\nIniciando carga de datos a {broker_host} en el tópico '{MQTT_TOPIC}'...")
    print("Todos los registros serán transmitidos con la HORA ACTUAL de publicación.")
    print("Presiona Ctrl+C para detener la carga.")
    
    total = len(records)
    success_count = 0
    
    # Crear cliente MQTT con una ID fija
    client = mqtt.Client(client_id="vps_iot_historical_uploader", clean_session=True)
    
    try:
        # Conectar una sola vez al broker en el puerto configurado
        client.connect(broker_host, MQTT_PORT, 60)
        client.loop_start()
        
        # Esperar a que se complete la conexión
        time.sleep(0.5)
        
        for idx, r in enumerate(records, start=1):
            # Obtener timestamp actual al momento de publicar (igual que en test_simulation.py)
            ts_now = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")
            
            payload = {
                "observacion": f"{OBSERVACION_BASE_URI}/{idx}",
                "sensor_id": r["sensor_id"],
                "valor": r["valor"],
                "timestamp": ts_now,
                "zona": r["zona"],
                "coordenadas": {
                    "latitud": r["latitud"],
                    "longitud": r["longitud"]
                }
            }
            
            # Publicar usando la conexión persistente
            client.publish(MQTT_TOPIC, payload=json.dumps(payload), qos=0)
            success_count += 1
            
            if idx % 100 == 0 or idx == total:
                print(f"Progreso: [{idx}/{total}] publicados con éxito.")
                
            # Pequeño sleep para regular la velocidad
            time.sleep(0.001)
            
        print("Finalizando envíos. Esperando vaciado del buffer de red...")
        time.sleep(2.0)
                
    except KeyboardInterrupt:
        print("\nCarga interrumpida por el usuario.")
    except Exception as e:
        print(f"\nError publicando mensaje MQTT: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        
    print(f"\n[OK] Simulación de históricos completada. {success_count} mensajes enviados.")

if __name__ == "__main__":
    broker_host, csv_path = obtener_host()
    
    records = parse_csv_file(csv_path)
    if not records:
        sys.exit(1)
        
    publicar_historicos(records, broker_host)
