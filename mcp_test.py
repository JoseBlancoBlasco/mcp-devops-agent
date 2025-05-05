import asyncio
import subprocess
import sys
import os
import json
import time
import signal
from dotenv import load_dotenv

async def test_mcp_server():
    """
    Script simple para probar el servidor MCP de Azure DevOps directamente.
    """
    # Cargar variables de entorno desde .env
    load_dotenv()
    
    print("Prueba básica del servidor MCP de Azure DevOps")
    print("----------------------------------------------")
    
    # Verificar configuración de Azure DevOps
    if not os.getenv("AZDO_PAT") or not os.getenv("AZDO_ORG"):
        print("ERROR: Necesitas configurar las variables de entorno AZDO_PAT y AZDO_ORG")
        print("Ejemplo:")
        print("  AZDO_PAT=tu_personal_access_token")
        print("  AZDO_ORG=https://dev.azure.com/tu_organizacion")
        return
    else:
        print(f"Usando organización: {os.getenv('AZDO_ORG')}")
        print(f"PAT configurado: {'Sí' if os.getenv('AZDO_PAT') else 'No'}")
    
    # Obtener la ruta del script actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(current_dir, "devops_server.py")
    
    print(f"Iniciando servidor MCP: {server_script}")
    
    # Iniciar el servidor como proceso en segundo plano
    server_process = subprocess.Popen(
        [sys.executable, server_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )
    
    # Esperar un momento para que el servidor se inicie
    print("Esperando a que el servidor se inicie (2 segundos)...")
    await asyncio.sleep(2)
    
    # Mensajes del protocolo MCP
    initialize_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "rootUri": None,
            "capabilities": {}
        }
    }
    
    list_tools_message = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "listTools",
        "params": {}
    }
    
    call_tool_message = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "callTool",
        "params": {
            "name": "list_projects",
            "arguments": {}
        }
    }
    
    try:
        # Recopilar la salida inicial del servidor para diagnóstico
        print("\nMensajes iniciales del servidor:")
        stdout_buffer = ""
        stderr_buffer = ""
        
        for _ in range(10):  # Intentar capturar algunas líneas iniciales
            if server_process.stdout.readable():
                line = server_process.stdout.readline().strip()
                if line:
                    stdout_buffer += line + "\n"
                    print(f"[stdout] {line}")
            
            if server_process.stderr.readable():
                line = server_process.stderr.readline().strip()
                if line:
                    stderr_buffer += line + "\n"
                    print(f"[stderr] {line}")
            
            # Verificar si el proceso terminó
            if server_process.poll() is not None:
                print(f"¡El servidor se cerró con código {server_process.returncode}!")
                break
                
            # Pequeña pausa
            await asyncio.sleep(0.1)
        
        # Si el servidor terminó, mostrar toda la salida y terminar
        if server_process.poll() is not None:
            stdout_rest = server_process.stdout.read()
            stderr_rest = server_process.stderr.read()
            
            if stdout_rest:
                print("\nSalida estándar adicional:")
                print(stdout_rest)
            
            if stderr_rest:
                print("\nErrores adicionales:")
                print(stderr_rest)
            
            print(f"\nEl servidor terminó prematuramente con código {server_process.returncode}")
            return
        
        # Paso 1: Inicializar
        print("\n1. Enviando mensaje de inicialización (initialize)...")
        init_msg = json.dumps(initialize_message) + "\n"
        server_process.stdin.write(init_msg)
        server_process.stdin.flush()
        
        print("Esperando respuesta (5 segundos máximo)...")
        start_time = time.time()
        init_response = None
        
        while time.time() - start_time < 5:
            line = server_process.stdout.readline().strip()
            if line:
                print(f"  Respuesta recibida: {line}")
                try:
                    init_response = json.loads(line)
                    break
                except json.JSONDecodeError:
                    print(f"  Error al decodificar la respuesta: {line}")
            await asyncio.sleep(0.1)
        
        if not init_response:
            print("  No se recibió respuesta a la inicialización")
            # Verificar si hay errores
            error_line = server_process.stderr.readline().strip()
            if error_line:
                print(f"  Error del servidor: {error_line}")
            return
        
        # Paso 2: Listar herramientas
        print("\n2. Enviando mensaje para listar herramientas (listTools)...")
        tools_msg = json.dumps(list_tools_message) + "\n"
        server_process.stdin.write(tools_msg)
        server_process.stdin.flush()
        
        print("Esperando respuesta (5 segundos máximo)...")
        start_time = time.time()
        tools_response = None
        
        while time.time() - start_time < 5:
            line = server_process.stdout.readline().strip()
            if line:
                print(f"  Respuesta recibida")
                try:
                    tools_response = json.loads(line)
                    break
                except json.JSONDecodeError:
                    print(f"  Error al decodificar la respuesta: {line}")
            await asyncio.sleep(0.1)
        
        if not tools_response:
            print("  No se recibió respuesta al listTools")
            # Verificar si hay errores
            error_line = server_process.stderr.readline().strip()
            if error_line:
                print(f"  Error del servidor: {error_line}")
            return
        
        # Mostrar las herramientas disponibles
        if "result" in tools_response:
            tools = tools_response["result"]
            print(f"\nHerramientas disponibles ({len(tools)}):")
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool['name']}: {tool['description']}")
        
        # Paso 3: Llamar a una herramienta
        print("\n3. Probando la herramienta 'list_projects'...")
        call_msg = json.dumps(call_tool_message) + "\n"
        server_process.stdin.write(call_msg)
        server_process.stdin.flush()
        
        print("Esperando respuesta (10 segundos máximo)...")
        start_time = time.time()
        tool_response = None
        
        while time.time() - start_time < 10:
            line = server_process.stdout.readline().strip()
            if line:
                print(f"  Respuesta recibida")
                try:
                    tool_response = json.loads(line)
                    break
                except json.JSONDecodeError:
                    print(f"  Error al decodificar la respuesta: {line}")
            await asyncio.sleep(0.1)
        
        if not tool_response:
            print("  No se recibió respuesta al callTool")
            # Verificar si hay errores
            error_line = server_process.stderr.readline().strip()
            if error_line:
                print(f"  Error del servidor: {error_line}")
            return
        
        # Mostrar el resultado de la herramienta
        if "result" in tool_response:
            print("\nResultado de list_projects:")
            # El resultado es una lista de objetos TextContent
            for content in tool_response["result"]:
                if content["type"] == "text":
                    print("-" * 50)
                    print(content["text"])
                    print("-" * 50)
    
    except BrokenPipeError:
        print("Error: Conexión interrumpida (Broken pipe). El servidor puede haber terminado inesperadamente.")
    except Exception as e:
        print(f"Error durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Terminar el proceso del servidor
        print("\nFinalizando el servidor...")
        if server_process.poll() is None:  # Si el proceso sigue en ejecución
            try:
                server_process.terminate()
                server_process.wait(timeout=3)
                print("Servidor terminado correctamente")
            except subprocess.TimeoutExpired:
                print("El servidor no respondió, forzando terminación...")
                server_process.kill()
                server_process.wait()
        else:
            print(f"El servidor ya había terminado con código: {server_process.returncode}")
        
        # Verificar si hay algún mensaje final en stderr
        stderr_content = server_process.stderr.read()
        if stderr_content:
            print("\nMensajes de error del servidor:")
            print(stderr_content)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())