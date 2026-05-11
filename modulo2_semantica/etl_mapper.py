from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import SOSA, XSD
import requests
import sys
import os

# Añadir el path raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import FUSEKI_UPDATE_URL, GEO, EX, SOSA as SOSA_URI
from modulo1_ingestion.database import SessionLocal, SensorData

# Definir Namespaces adicionales
GEO_NS = Namespace(GEO)
EX_NS = Namespace(EX)

def map_to_rdf():
    db = SessionLocal()
    datos = db.query(SensorData).all() # En producción podrías filtrar solo los nuevos

    if not datos:
        print("No hay datos nuevos para procesar.")
        return

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
            g.add((feature_uri, RDF.type, GEO_NS.Feature))
            g.add((feature_uri, GEO_NS.hasGeometry, EX_NS[f"geometry/{dato.id}"]))
            g.add((EX_NS[f"geometry/{dato.id}"], GEO_NS.asWKT, point_wkt))
            g.add((obs_uri, SOSA.hasFeatureOfInterest, feature_uri))

    # Serializar a formato Turtle para enviar a Fuseki
    turtle_data = g.serialize(format="turtle")

    # Enviar a Fuseki (SPARQL Update)
    # Nota: Esto asume que el dataset está creado en Fuseki
    update_query = f"INSERT DATA {{ {g.serialize(format='nt')} }}"
    
    try:
        response = requests.post(
            FUSEKI_UPDATE_URL,
            data={'update': update_query},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        if response.status_code == 200 or response.status_code == 204:
            print(f"Éxito: Se enviaron {len(datos)} registros a Fuseki.")
        else:
            print(f"Error en Fuseki: {response.text}")
    except Exception as e:
        print(f"No se pudo conectar con Fuseki: {e}")

    db.close()

if __name__ == "__main__":
    map_to_rdf()
