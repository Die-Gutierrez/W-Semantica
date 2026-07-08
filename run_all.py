import sys
import os
import subprocess
import time
import threading

def log_output(process, prefix):
    # Leer línea por línea la salida del subproceso
    for line in iter(process.stdout.readline, b''):
        try:
            # Decodificar usando utf-8
            msg = line.decode('utf-8', errors='replace').rstrip()
            # Limpiar caracteres incompatibles con la codificación de la consola actual
            encoding = sys.stdout.encoding or 'utf-8'
            clean_msg = msg.encode(encoding, errors='replace').decode(encoding)
            print(f"[{prefix}] {clean_msg}")
        except Exception:
            try:
                # Fallback seguro en ascii
                msg = line.decode('ascii', errors='replace').rstrip()
                print(f"[{prefix}] {msg}")
            except Exception:
                pass

def main():
    # Asegurar que el directorio de trabajo actual sea la raíz del proyecto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir:
        os.chdir(script_dir)
    
    processes = []
    
    # Definir los módulos a ejecutar (Nombre, Ruta del script)
    services = [
        ("SUBSCRIBER", "modulo1_ingestion/subscriber.py"),
        ("ETL_MAPPER", "modulo2_semantica/etl_mapper.py"),
        ("API", "modulo3_api/main.py")
    ]
    
    print("================================================================")
    print("       Orquestador Semántico IoT - Control de Servicios        ")
    print("================================================================")
    
    # Iniciar cada servicio usando subprocess.Popen y el flag "-u" de python (salida sin búfer)
    for name, script_path in services:
        print(f"[Orquestador] Iniciando {name} ({script_path})...")
        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            processes.append((proc, name))
        except Exception as e:
            print(f"[Orquestador] ERROR al iniciar {name}: {e}")
        
    # Crear e iniciar hilos en segundo plano para redirigir los logs de cada servicio
    threads = []
    for proc, name in processes:
        t = threading.Thread(target=log_output, args=(proc, name), daemon=True)
        t.start()
        threads.append(t)
        
    print("[Orquestador] Todos los servicios han sido iniciados.")
    print("[Orquestador] Presiona Ctrl+C para detener todos los servicios de forma limpia.")
    print("================================================================")
    
    # Mantener el script activo y monitorear fallos inesperados
    try:
        while True:
            for proc, name in processes:
                exit_code = proc.poll()
                if exit_code is not None:
                    print(f"[Orquestador] ¡ADVERTENCIA! El servicio {name} se detuvo con código {exit_code}.")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[Orquestador] Interrupción detectada (Ctrl+C). Deteniendo servicios...")
    finally:
        # Intentar detener amigablemente todos los servicios activos
        for proc, name in processes:
            if proc.poll() is None:
                print(f"[Orquestador] Enviando señal de terminación a {name}...")
                proc.terminate()
                
        # Esperar a que terminen o forzar su cierre
        for proc, name in processes:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print(f"[Orquestador] {name} no respondió a terminate. Forzando detención (kill)...")
                proc.kill()
                
        print("[Orquestador] Todos los procesos secundarios han sido detenidos con éxito.")

if __name__ == "__main__":
    main()
