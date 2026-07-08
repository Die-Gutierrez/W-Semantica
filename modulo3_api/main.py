# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
import requests
import sys
import os

# Añadir el path raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import FUSEKI_QUERY_URL

app = FastAPI(title="Geo-Semantic IoT API", version="1.0.0")

# Integrar Scalar para la documentación interactiva
# pyrefly: ignore [missing-import]
from scalar_fastapi import get_scalar_api_reference, Theme

@app.get("/scalar", include_in_schema=False)
def get_scalar_documentation():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
        theme=Theme.DEEP_SPACE,
    )

@app.get(
    "/api/v1/sensors/points",
    summary="Obtener puntos registrados con límite (JSON)",
    description="Devuelve los puntos registrados en formato JSON. Permite configurar cuántos elementos devolver usando el parámetro de consulta 'id' (por defecto 10)."
)
def get_sensors_points(id: int = 10):
    # Consulta SPARQL para obtener los puntos registrados con un límite
    query = f"""
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX ex: <http://example.org/unjbg/>

    SELECT ?obs ?sensor ?valor ?timestamp ?wkt ?zona
    WHERE {{
      ?obs a sosa:Observation ;
           sosa:madeBySensor ?sensor ;
           sosa:hasSimpleResult ?valor ;
           sosa:resultTime ?timestamp ;
           sosa:hasFeatureOfInterest ?feature .
      ?sensor geo:hasGeometry ?geom .
      ?geom geo:asWKT ?wkt .
      BIND(STRAFTER(STR(?feature), "zona/") AS ?zona) .
    }}
    ORDER BY DESC(?timestamp)
    LIMIT {id}
    """
    try:
        response = requests.get(
            FUSEKI_QUERY_URL,
            params={'query': query, 'format': 'json'}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error consultando el Triplestore")

        results = response.json()
        history = []
        for row in results["results"]["bindings"]:
            wkt = row["wkt"]["value"]
            coords_str = wkt.replace("POINT(", "").replace(")", "")
            lon, lat = map(float, coords_str.split())
            
            history.append({
                "observacion": row["obs"]["value"],
                "sensor_id": row["sensor"]["value"].split("/")[-1],
                "valor": float(row["valor"]["value"]),
                "timestamp": row["timestamp"]["value"],
                "zona": row["zona"]["value"],
                "coordenadas": {
                    "latitud": lat,
                    "longitud": lon
                }
            })
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/v1/sensors/history",
    summary="Obtener todo el historial de lecturas (JSON)",
    description="Devuelve el historial completo de observaciones almacenadas en formato JSON, ordenadas cronológicamente."
)
def get_sensors_history():
    # Consulta SPARQL para obtener el historial completo sin límite
    query = """
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX ex: <http://example.org/unjbg/>

    SELECT ?obs ?sensor ?valor ?timestamp ?wkt ?zona
    WHERE {
      ?obs a sosa:Observation ;
           sosa:madeBySensor ?sensor ;
           sosa:hasSimpleResult ?valor ;
           sosa:resultTime ?timestamp ;
           sosa:hasFeatureOfInterest ?feature .
      ?sensor geo:hasGeometry ?geom .
      ?geom geo:asWKT ?wkt .
      BIND(STRAFTER(STR(?feature), "zona/") AS ?zona) .
    }
    ORDER BY DESC(?timestamp)
    """
    try:
        response = requests.get(
            FUSEKI_QUERY_URL,
            params={'query': query, 'format': 'json'}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error consultando el Triplestore")

        results = response.json()
        history = []
        for row in results["results"]["bindings"]:
            wkt = row["wkt"]["value"]
            coords_str = wkt.replace("POINT(", "").replace(")", "")
            lon, lat = map(float, coords_str.split())
            
            history.append({
                "observacion": row["obs"]["value"],
                "sensor_id": row["sensor"]["value"].split("/")[-1],
                "valor": float(row["valor"]["value"]),
                "timestamp": row["timestamp"]["value"],
                "zona": row["zona"]["value"],
                "coordenadas": {
                    "latitud": lat,
                    "longitud": lon
                }
            })
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/v1/sensors/history/{sensor_id}",
    summary="Obtener historial por ID de sensor (JSON)",
    description="Filtra las observaciones para un sensor específico y devuelve los datos en formato JSON. Soporta un parámetro numérico 'limit' para restringir los resultados (por defecto 10)."
)
def get_sensor_history_by_id(sensor_id: str, limit: int = 10):
    # Consulta SPARQL para obtener historial filtrado por sensor_id y limitado
    query = f"""
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX ex: <http://example.org/unjbg/>

    SELECT ?obs ?sensor ?valor ?timestamp ?wkt ?zona
    WHERE {{
      ?obs a sosa:Observation ;
           sosa:madeBySensor ?sensor ;
           sosa:hasSimpleResult ?valor ;
           sosa:resultTime ?timestamp ;
           sosa:hasFeatureOfInterest ?feature .
      ?sensor geo:hasGeometry ?geom .
      ?geom geo:asWKT ?wkt .
      BIND(STRAFTER(STR(?feature), "zona/") AS ?zona) .
      FILTER(STRENDS(STR(?sensor), CONCAT("/", "{sensor_id}")))
    }}
    ORDER BY DESC(?timestamp)
    LIMIT {limit}
    """
    try:
        response = requests.get(
            FUSEKI_QUERY_URL,
            params={'query': query, 'format': 'json'}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error consultando el Triplestore")

        results = response.json()
        history = []
        for row in results["results"]["bindings"]:
            wkt = row["wkt"]["value"]
            coords_str = wkt.replace("POINT(", "").replace(")", "")
            lon, lat = map(float, coords_str.split())
            
            history.append({
                "observacion": row["obs"]["value"],
                "valor": float(row["valor"]["value"]),
                "timestamp": row["timestamp"]["value"],
                "zona": row["zona"]["value"],
                "coordenadas": {
                    "latitud": lat,
                    "longitud": lon
                }
            })
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/v1/sensors/observation/{observation_id}",
    summary="Ver una lectura específica (JSON)",
    description="Recupera los detalles de una única observación en formato JSON utilizando su identificador numérico."
)
def get_sensor_observation_by_id(observation_id: int):
    # Consulta SPARQL para obtener una observación específica por su ID numérico
    query = f"""
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX ex: <http://example.org/unjbg/>

    SELECT ?sensor ?valor ?timestamp ?wkt ?zona
    WHERE {{
      <http://example.org/unjbg/observation/{observation_id}> a sosa:Observation ;
                                     sosa:madeBySensor ?sensor ;
                                     sosa:hasSimpleResult ?valor ;
                                     sosa:resultTime ?timestamp ;
                                     sosa:hasFeatureOfInterest ?feature .
      ?sensor geo:hasGeometry ?geom .
      ?geom geo:asWKT ?wkt .
      BIND(STRAFTER(STR(?feature), "zona/") AS ?zona) .
    }}
    """
    try:
        response = requests.get(
            FUSEKI_QUERY_URL,
            params={'query': query, 'format': 'json'}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error consultando el Triplestore")

        results = response.json()
        bindings = results["results"]["bindings"]
        
        if not bindings:
            raise HTTPException(status_code=404, detail="Observación no encontrada")
            
        row = bindings[0]
        wkt = row["wkt"]["value"]
        coords_str = wkt.replace("POINT(", "").replace(")", "")
        lon, lat = map(float, coords_str.split())
        
        return {
            "observacion": f"http://example.org/unjbg/observation/{observation_id}",
            "sensor_id": row["sensor"]["value"].split("/")[-1],
            "valor": float(row["valor"]["value"]),
            "timestamp": row["timestamp"]["value"],
            "zona": row["zona"]["value"],
            "coordenadas": {
                "latitud": lat,
                "longitud": lon
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run("modulo3_api.main:app", host="0.0.0.0", port=8000, reload=True)
