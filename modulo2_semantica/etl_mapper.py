# pyrefly: ignore [missing-import]
from rdflib import Graph, Literal, RDF, URIRef, Namespace
# pyrefly: ignore [missing-import]
from rdflib.namespace import SOSA, XSD
import requests
import sys
import os

# Añadir el path raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import FUSEKI_UPDATE_URL, GEO, EX, SOSA as SOSA_URI, BASE_DIR
from modulo1_ingestion.database import SessionLocal, SensorData

# Definir Namespaces adicionales
GEO_NS = Namespace(GEO)
EX_NS = Namespace(EX)

def map_to_rdf(last_id=0):
    db = SessionLocal()
    # Filtrar para obtener solo registros nuevos (id > last_id) ordenados ascendentemente
    datos = db.query(SensorData).filter(SensorData.id > last_id).order_by(SensorData.id.asc()).all()

    if not datos:
        db.close()
        return last_id

    g = Graph()
    g.bind("sosa", SOSA)
    g.bind("geo", GEO_NS)
    g.bind("ex", EX_NS)

    for dato in datos:
        # Definir URIs
        sensor_uri = EX_NS[f"sensor/{dato.sensor_id}"]
        obs_uri = EX_NS[f"observation/{dato.id}"]
        feature_uri = EX_NS[f"zona/{dato.zona}"]

        # 1. El Sensor
        g.add((sensor_uri, RDF.type, SOSA.Sensor))

        # 2. La Observación
        g.add((obs_uri, RDF.type, SOSA.Observation))
        g.add((obs_uri, SOSA.madeBySensor, sensor_uri))
        g.add((obs_uri, SOSA.hasSimpleResult, Literal(dato.valor, datatype=XSD.float)))
        g.add((obs_uri, SOSA.resultTime, Literal(dato.timestamp.isoformat(), datatype=XSD.dateTime)))

        # 3. Ubicación (GeoSPARQL)
        if dato.latitud and dato.longitud:
            point_wkt = Literal(f"POINT({dato.longitud} {dato.latitud})", datatype=GEO_NS.wktLiteral)
            # Asociamos la geometría a la Observación de forma dinámica
            g.add((obs_uri, RDF.type, GEO_NS.Feature))
            g.add((obs_uri, GEO_NS.hasGeometry, EX_NS[f"geometry/obs_{dato.id}"]))
            g.add((EX_NS[f"geometry/obs_{dato.id}"], GEO_NS.asWKT, point_wkt))
            g.add((obs_uri, SOSA.hasFeatureOfInterest, feature_uri))

    # Serializar a N-Triples para Fuseki (es más liviano y seguro para SPARQL INSERT DATA)
    update_query = f"INSERT DATA {{ {g.serialize(format='nt')} }}"
    
    new_last_id = last_id
    try:
        response = requests.post(
            FUSEKI_UPDATE_URL,
            data={'update': update_query},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10
        )
        if response.status_code == 200 or response.status_code == 204:
            new_last_id = datos[-1].id
            print(f"Éxito: Se enviaron {len(datos)} nuevos registros a Fuseki (Último ID: {new_last_id}).")
        else:
            print(f"Error en Fuseki (Código {response.status_code}): {response.text}")
    except requests.exceptions.Timeout:
        print("Error: Tiempo de espera agotado al conectar con Fuseki (Timeout).")
    except Exception as e:
        print(f"No se pudo conectar con Fuseki: {e}")

    db.close()
    return new_last_id

if __name__ == "__main__":
    import time
    
    print("==================================================")
    print("   ETL Mapper Semántico Continuo e Incremental    ")
    print("==================================================")
    print("Iniciando monitoreo de base de datos SQLite...")
    
    # Ruta del archivo para persistir el progreso del ETL
    LAST_ID_FILE = os.path.join(BASE_DIR, "etl_last_id.txt")
    last_processed_id = 0
    
    # Intentar cargar el último ID procesado al iniciar
    if os.path.exists(LAST_ID_FILE):
        try:
            with open(LAST_ID_FILE, "r") as f:
                last_processed_id = int(f.read().strip())
            print(f"Progreso cargado. Continuando desde el ID de SQLite: {last_processed_id}")
        except Exception as e:
            print(f"No se pudo leer {LAST_ID_FILE}, iniciando desde 0. Detalle: {e}")
    else:
        print("No se encontró archivo de progreso previo, iniciando desde ID 0.")
        
    try:
        while True:
            new_id = map_to_rdf(last_processed_id)
            if new_id != last_processed_id:
                last_processed_id = new_id
                # Guardar progreso en el archivo
                try:
                    with open(LAST_ID_FILE, "w") as f:
                        f.write(str(last_processed_id))
                except Exception as e:
                    print(f"Error al persistir progreso en {LAST_ID_FILE}: {e}")
            time.sleep(3) # Polling cada 3 segundos
    except KeyboardInterrupt:
        print("\nServicio ETL de Monitoreo continuo finalizado correctamente.")

