import os
import signal
import sys
import subprocess
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class DevOpsMCPServer:
    def __init__(self, command="python -m mcp.server", host="localhost", port=8080):
        """
        Inicializar servidor MCP
        
        Args:
            command: Comando para iniciar el servidor MCP (como string)
            host: Host donde se ejecutará el servidor (solo informativo)
            port: Puerto donde se ejecutará el servidor (solo informativo)
        """
        self.command = command
        self.host = host
        self.port = port
        self.process = None
        
    def start(self):
        """Iniciar el servidor MCP usando subprocess"""
        print(f"Iniciando servidor MCP en {self.host}:{self.port}...")
        
        # Iniciar el servidor como un proceso separado
        try:
            # Usar subprocess.Popen para ejecutar el comando
            self.process = subprocess.Popen(
                self.command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy()
            )
            print(f"Servidor MCP iniciado (PID: {self.process.pid})")
        except Exception as e:
            print(f"Error al iniciar el servidor MCP: {str(e)}")
            raise
        
    def stop(self):
        """Detener el servidor MCP"""
        if self.process:
            print("Deteniendo servidor MCP...")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("Servidor MCP detenido correctamente")
            except Exception as e:
                print(f"Error al detener el servidor MCP: {str(e)}")
                try:
                    self.process.kill()
                    print("Servidor MCP terminado forzosamente")
                except:
                    pass

def signal_handler(sig, frame):
    """Manejar señal de interrupción para detener el servidor limpiamente"""
    print("\nRecibida señal de interrupción. Deteniendo servidor...")
    if 'mcp_server' in globals() and mcp_server is not None:
        mcp_server.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Registrar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Iniciar servidor
    mcp_server = DevOpsMCPServer()
    mcp_server.start()
    
    try:
        # Mantener servidor activo
        print("Presione Ctrl+C para detener el servidor")
        signal.pause()  # Esperar señales
    except (KeyboardInterrupt, SystemExit):
        mcp_server.stop()