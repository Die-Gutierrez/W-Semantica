# Dependencias del Proyecto

Para que el sistema funcione, instalamos estas librerías clave:

1. **paho-mqtt**: Permite que Python hable el protocolo MQTT. Sin ella, no podríamos recibir datos del ESP32 o del simulador.
2. **SQLAlchemy**: Facilita el trabajo con la base de datos SQLite. Nos permite guardar datos usando objetos de Python en lugar de escribir código SQL manual.
3. **rdflib**: Es la librería más importante para la Web Semántica en Python. Permite crear el "Grafo" de conocimiento (tripletas RDF).
4. **requests**: Se usa para enviar los datos RDF ya procesados hacia el servidor Apache Jena Fuseki a través de la red.
5. **FastAPI & Uvicorn**: Crean el servidor web de alta velocidad para la API final.
6. **python-dotenv**: Permite manejar configuraciones y contraseñas de forma segura (opcional).
