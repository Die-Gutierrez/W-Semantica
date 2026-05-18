# Guía de Configuración: Apache Jena Fuseki

Para que el proyecto funcione, Fuseki debe estar configurado como nuestro "Triplestore" oficial. Sigue estos pasos:

## 1. Instalación

- Descomprime el archivo `.zip` en una carpeta como `C:\fuseki`.
- Asegúrate de tener Java instalado (`java -version` en la terminal).

> [!TIP]
> Si tienes problemas con la versión de Java o no la tienes instalada, descarga e instala **OpenJDK 21 (LTS)** utilizando uno de los siguientes enlaces oficiales y permanentes:
>
> - **[Página oficial de descargas de Adoptium](https://adoptium.net/temurin/releases/?version=21)** (Selecciona Windows y el formato `.msi` para una instalación sencilla).

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
