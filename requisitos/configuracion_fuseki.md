# Guía de Configuración: Apache Jena Fuseki

Para que el proyecto funcione, Fuseki debe estar configurado como nuestro "Triplestore" oficial. Sigue estos pasos:

## 1. Instalación

- Descomprime el archivo `.zip` en una carpeta como `C:\fuseki`.
- Asegúrate de tener Java instalado (`java -version` en la terminal).

En el caso se tenga problemas con la versiòn de java descargar es instalar el siguiente: https://release-assets.githubusercontent.com/github-production-release-asset/602574963/c6fdcf73-1544-4c6d-9246-83b23d2456ba?sp=r&sv=2018-11-09&sr=b&spr=https&se=2026-05-11T15%3A08%3A01Z&rscd=attachment%3B+filename%3DOpenJDK21U-jdk_x64_windows_hotspot_21.0.3_9.msi&rsct=application%2Foctet-stream&skoid=96c2d410-5711-43a1-aedd-ab1947aa7ab0&sktid=398a6654-997b-47e9-b12b-9515b896b4de&skt=2026-05-11T14%3A07%3A05Z&ske=2026-05-11T15%3A08%3A01Z&sks=b&skv=2018-11-09&sig=yiatfVDWyEJpCImwRYnhEWgNhSrjTgkZajzaw3dP7kA%3D&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmVsZWFzZS1hc3NldHMuZ2l0aHVidXNlcmNvbnRlbnQuY29tIiwia2V5Ijoia2V5MSIsImV4cCI6MTc3ODUxMjkzOSwibmJmIjoxNzc4NTA5MzM5LCJwYXRoIjoicmVsZWFzZWFzc2V0cHJvZHVjdGlvbi5ibG9iLmNvcmUud2luZG93cy5uZXQifQ.fZVxCKI1-iEvsNkQepAZ_5W7QNw_0taj_s1xSjLbMpA&response-content-disposition=attachment%3B%20filename%3DOpenJDK21U-jdk_x64_windows_hotspot_21.0.3_9.msi&response-content-type=application%2Foctet-stream

## 2. Inicio del Servidor

Ejecuta el script de inicio:

```powershell
.\fuseki-server.bat
```

Verás un mensaje indicando que el servidor está corriendo en el puerto **3030**.

## 3. Configuración del Dataset (CRUCIAL)

El código de Python busca un dataset específico. Debes crearlo manualmente la primera vez:

1. Abre [http://localhost:3030](http://localhost:3030).
2. Ve a la pestaña **"Manage datasets"**.
3. Presiona **"add new dataset"**.
4. **Dataset Name**: `iot_sensores` (debe ser exacto).
5. **Dataset Type**: `Persistent (TDB2)`.
6. Haz clic en **"Create Dataset"**.

## 4. Verificación

Una vez creado, verás que tienes endpoints para:

- `/iot_sensores/query` (Para consultas SPARQL).
- `/iot_sensores/update` (Para insertar datos).

Estos son los mismos que están configurados en tu archivo `common/config.py`.
