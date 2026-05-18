# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
import requests
import sys
import os

# Añadir el path raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import FUSEKI_QUERY_URL

app = FastAPI(title="Geo-Semantic IoT API", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "API Semántica Geoespacial activa"}

@app.get("/api/v1/sensors/geojson")
def get_sensors_geojson():
    # Consulta SPARQL para obtener sensores, valores y geometrías
    query = """
    PREFIX sosa: <http://www.w3.org/ns/sosa/>
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    PREFIX ex: <http://example.org/unjbg/>

    SELECT ?sensor ?valor ?wkt ?zona
    WHERE {
      ?obs a sosa:Observation ;
           sosa:madeBySensor ?sensor ;
           sosa:hasSimpleResult ?valor ;
           sosa:hasFeatureOfInterest ?feature .
      ?feature geo:hasGeometry ?geom ;
               BIND(STRAFTER(STR(?feature), "zona/") AS ?zona) .
      ?geom geo:asWKT ?wkt .
    }
    """

    try:
        response = requests.get(
            FUSEKI_QUERY_URL,
            params={'query': query, 'format': 'json'}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error consultando el Triplestore")

        results = response.json()
        
        # Transformar a GeoJSON
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for row in results["results"]["bindings"]:
            wkt = row["wkt"]["value"] # Ejemplo: POINT(-70.25 -18.01)
            # Extraer coordenadas de WKT simple
            coords_str = wkt.replace("POINT(", "").replace(")", "")
            lon, lat = map(float, coords_str.split())

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "sensor": row["sensor"]["value"],
                    "valor": float(row["valor"]["value"]),
                    "zona": row["zona"]["value"]
                }
            }
            geojson["features"].append(feature)

        return geojson

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
