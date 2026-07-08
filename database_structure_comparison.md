# Comparativa de Estructuras de Base de Datos: IoT vs. Reportes de la App

Este documento realiza un análisis comparativo y de integración semántica entre las dos principales fuentes de datos en tiempo real de la plataforma:
1. **IoT Sensor Data** (Esquema original de mediciones de sensores físicos ESP32).
2. **Base de Datos de la Aplicación de Seguridad** (Datos de [tablas_app.txt](file:///c:/Users/denni/Documents/WebSemantica/W-Semantica/tablas_app.txt) con reportes ciudadanos).

---

## 📊 1. Esquemas Relacionales Comparados

A continuación se contrastan las estructuras de ambas bases de datos relacionales:

### A. Sensores de IoT (`sensor_data`)
Almacena lecturas numéricas continuas y automatizadas de telemetría de dispositivos físicos.
```sql
CREATE TABLE sensor_data (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sensor_id VARCHAR(50) NOT NULL,                  -- ID físico del chip ESP32
  zona VARCHAR(10) NOT NULL,                       -- Clasificación zonal (X, Y, Z)
  valor FLOAT NOT NULL,                            -- Valor medido (ej: movimiento o nivel)
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,    -- Momento exacto de la lectura
  latitud FLOAT,                                   -- Coordenada GPS Y
  longitud FLOAT                                   -- Coordenada GPS X
);
```

### B. Base de Datos de la Aplicación de Seguridad (`reports`)
Almacena reportes de incidentes críticos de seguridad enviados manualmente por los usuarios a través de la aplicación móvil/web.
```sql
CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,                           -- Identificador del usuario que reporta
  report_type TEXT NOT NULL,                       -- Tipo ('INCENDIO', 'ASALTO', 'ACCIDENTE', 'OTRO')
  address TEXT NOT NULL,                           -- Dirección aproximada
  reference TEXT,                                  -- Referencia espacial
  latitude DOUBLE PRECISION NOT NULL,              -- Coordenada de precisión Y
  longitude DOUBLE PRECISION NOT NULL,             -- Coordenada de precisión X
  description TEXT,                                -- Detalle textual del incidente
  reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),   -- Fecha/Hora del reporte
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 🔄 2. Mapeo Conceptual de Entidades

Ambos modelos capturan eventos en el espacio y en el tiempo, pero difieren en su origen (automatizado vs. humano) y tipo de dato:

| Concepto | IoT (`sensor_data`) | App Ciudadana (`reports`) | Tipo de Diferencia |
| :--- | :--- | :--- | :--- |
| **Origen del Dato** | Dispositivo automático (Sensor ESP32) | Usuario humano (Ciudadano/Policía) | **Físico vs. Social** |
| **Identificación** | `sensor_id` (String de hardware) | `user_id` (UUID del reportero) | **Dispositivo vs. Agente** |
| **Tipo de Evento** | Medición física continua | Incidente de seguridad discreto | **Métrica vs. Categoría** |
| **Naturaleza del Valor**| `valor` (Numérico / Float) | `report_type` (Categórico / Enums) | **Medición vs. Clasificación** |
| **Ubicación** | `latitud`, `longitud` (Punto fijo) | `latitude`, `longitude` (Punto variable) | **Sensor estático vs. GPS dinámico** |
| **Granularidad Temporal**| Frecuente (segundos/minutos) | Esporádica (según ocurrencia) | **Transmisión continua vs. Evento único** |

---

## 🧠 3. Ontología y Grafo Semántico Integrado

En la Web Semántica, podemos integrar ambas fuentes bajo un mismo grafo RDF utilizando las ontologías estándar **SOSA** (para los sensores) y **GeoSPARQL** (para las ubicaciones espaciales comunes).

```mermaid
graph TD
    subgraph SENSORES IOT (SOSA)
        obs[ex:observacion/1] -->|a| sosaObs[sosa:Observation]
        obs -->|sosa:madeBySensor| sensor[ex:sensor/ESP32_01]
        obs -->|sosa:hasSimpleResult| val[85.5]
        obs -->|sosa:resultTime| t1["2026-07-06T22:58:00Z"]
    end

    subgraph REPORTES CIUDADANOS (APLICACION)
        rep[ex:reporte/UUID] -->|a| repClass[ex:ReporteCiudadano]
        rep -->|ex:tipoReporte| type["ASALTO"]
        rep -->|ex:creadoPor| reporter[ex:reportero/UUID]
        rep -->|ex:fechaReporte| t2["2026-07-06T22:58:53Z"]
    end

    subgraph GEOMETRIA COMUN (GeoSPARQL)
        obs -->|sosa:hasFeatureOfInterest| loc[ex:ubicacion/Tacna_LaUnion]
        rep -->|ex:ocurrioEn| loc
        loc -->|a| geoFeat[geo:Feature]
        loc -->|geo:hasGeometry| geom[ex:geometry/LaUnion]
        geom -->|geo:asWKT| wkt["POINT(-70.231 17.973)"]
    end
```

### Estrategia de Enlace Semántico:
1. **Punto de Unión Geoespacial (`geo:Feature`)**: Ambos flujos de datos generan puntos en coordenadas geográficas. Al asociarlos a una entidad espacial común (`ex:ubicacion/...`), conectamos las lecturas de los dispositivos físicos con los reportes manuales en el mapa.
2. **Correlación de Eventos**: Podemos mapear que la activación de una alerta/sensor (ej. sirenas comunitarias IoT o sensores de presencia) se corresponde temporal y espacialmente con la creación de un reporte de asalto o accidente.

---

## 💡 4. Caso de Uso: Correlación Cruzada (SPARQL)

Este cruce semántico permite automatizar alertas. Por ejemplo, podemos consultar en Fuseki qué sensores detectaron actividad (movimiento/valor alto) en el mismo lugar y momento (ventana de 5 minutos) en que un ciudadano generó un reporte de incidente desde la app. Esto sirve para **autenticar alarmas automáticas**:

```sparql
PREFIX ex: <http://example.org/unjbg/>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?sensor ?tipoReporte ?ubicacionComun ?tiempoSensor ?tiempoReporte
WHERE {
  # 1. Obtener la observación del sensor IoT
  ?obs a sosa:Observation ;
       sosa:madeBySensor ?sensor ;
       sosa:resultTime ?tiempoSensor ;
       sosa:hasFeatureOfInterest ?ubicacionComun .

  # 2. Obtener el reporte de la aplicación en el mismo lugar
  ?reporte a ex:ReporteCiudadano ;
           ex:tipoReporte ?tipoReporte ;
           ex:fechaReporte ?tiempoReporte ;
           ex:ocurrioEn ?ubicacionComun .

  # 3. Filtrar que hayan ocurrido en una ventana de tiempo cercana
  BIND(xsd:dateTime(?tiempoSensor) AS ?tSensor)
  BIND(xsd:dateTime(?tiempoReporte) AS ?tReporte)
  FILTER(?tReporte >= ?tSensor && ?tReporte <= ?tSensor + "PT5M"^^xsd:duration)
}
```
