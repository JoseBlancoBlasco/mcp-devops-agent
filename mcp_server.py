import os
import signal
import sys
import subprocess
import asyncio
from dotenv import load_dotenv
from azdo_tools import AzureDevOpsTool, register_azdo_tools_with_mcp
import json

# Importaciones para MCP según la API oficial
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

# Cargar variables de entorno
load_dotenv()

# Implementación de handlers para las herramientas de Azure DevOps
async def list_repositories_handler(azdo_tool, args=None):
    """Handler para listar repositorios"""
    try:
        if not args:
            args = {}
        project = args.get("project")
        date_filter = args.get("date_filter")
        
        repositories = azdo_tool.list_repositories(project, date_filter)
        return {"status": "success", "data": repositories}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_work_item_handler(azdo_tool, args=None):
    """Handler para obtener detalles de un work item"""
    try:
        if not args or "id" not in args:
            return {"status": "error", "message": "Se requiere un ID de work item"}
            
        work_item_id = args["id"]
        project = args.get("project")
        
        work_item = azdo_tool.get_work_item(work_item_id, project)
        
        # Formatear el resultado para que sea más fácil de entender
        formatted_item = {
            "id": work_item.get("id"),
            "title": work_item.get("fields", {}).get("System.Title", "Sin título"),
            "state": work_item.get("fields", {}).get("System.State", "Desconocido"),
            "type": work_item.get("fields", {}).get("System.WorkItemType", "Desconocido"),
            "assignedTo": work_item.get("fields", {}).get("System.AssignedTo", {}).get("displayName", "No asignado") if isinstance(work_item.get("fields", {}).get("System.AssignedTo"), dict) else "No asignado",
            "createdDate": work_item.get("fields", {}).get("System.CreatedDate", "Fecha desconocida"),
            "description": work_item.get("fields", {}).get("System.Description", "Sin descripción")
        }
        
        return {"status": "success", "data": formatted_item}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
async def list_work_items_handler(azdo_tool, args=None):
    """Handler para listar work items"""
    try:
        if not args:
            args = {}
        
        project = args.get("project")
        query = args.get("query")
        work_item_type = args.get("work_item_type")
        date_filter = args.get("date_filter")
        state = args.get("state")
                
        work_items = azdo_tool.list_work_items(query, project, work_item_type, date_filter, state)
        result = []
        
        for wi in work_items:
            result.append({
                "id": wi.get("id"),
                "title": wi.get("fields", {}).get("System.Title", "Sin título"),
                "state": wi.get("fields", {}).get("System.State", "Desconocido"),
                "type": wi.get("fields", {}).get("System.WorkItemType", "Desconocido"),
                "assignedTo": wi.get("fields", {}).get("System.AssignedTo", {}).get("displayName", "No asignado") if isinstance(wi.get("fields", {}).get("System.AssignedTo"), dict) else "No asignado",
                "createdDate": wi.get("fields", {}).get("System.CreatedDate", "Fecha desconocida")
            })
                
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
async def list_recent_work_items_handler(azdo_tool, args=None):
    """Handler para listar los work items más recientes"""
    try:
        if not args:
            args = {}
            
        limit = args.get("limit", 10)
        work_item_type = args.get("work_item_type")
        state = args.get("state")
        project = args.get("project")
        
        # Realizar la búsqueda
        work_items = azdo_tool.list_work_items(
            query_string=None,
            project=project,
            work_item_type=work_item_type,
            date_filter="last 30 days",  # Por defecto últimos 30 días
            state=state
        )
        
        # Limitar a la cantidad solicitada
        work_items = work_items[:limit] if work_items and len(work_items) > limit else work_items
        
        # Formatear la respuesta
        result = []
        for wi in work_items:
            result.append({
                "id": wi.get("id"),
                "title": wi.get("fields", {}).get("System.Title", "Sin título"),
                "state": wi.get("fields", {}).get("System.State", "Desconocido"),
                "type": wi.get("fields", {}).get("System.WorkItemType", "Desconocido"),
                "assignedTo": wi.get("fields", {}).get("System.AssignedTo", {}).get("displayName", "No asignado") if isinstance(wi.get("fields", {}).get("System.AssignedTo"), dict) else "No asignado",
                "createdDate": wi.get("fields", {}).get("System.CreatedDate", "Fecha desconocida")
            })
                
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
async def list_pipelines_handler(azdo_tool, args=None):
    """Handler para listar pipelines"""
    try:
        if not args:
            args = {}
            
        project = args.get("project")
        date_filter = args.get("date_filter")
                
        pipelines = azdo_tool.list_pipelines(project, date_filter)
        result = [{"name": pipeline.get("name"), "id": pipeline.get("id")} for pipeline in pipelines]
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
async def list_available_tools_handler(azdo_tool, args=None):
    """Handler para listar las herramientas disponibles"""
    try:
        tools = [
            {
                "name": "list_repositories",
                "description": "Lista repositorios de Azure DevOps con opciones de filtrado por fecha"
            },
            {
                "name": "list_work_items", 
                "description": "Lista work items con filtrado por tipo, fecha, proyecto y estado"
            },
            {
                "name": "list_pipelines",
                "description": "Lista pipelines de Azure DevOps con filtrado por fecha"
            },
            {
                "name": "get_work_item",
                "description": "Obtiene detalles de un work item específico por su ID"
            },
            {
                "name": "list_recent_work_items",
                "description": "Lista los work items más recientes (hasta un límite especificado)"
            }
        ]
        return {"status": "success", "data": tools}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
        self.tools = {}
        self.server_params = None
        self.mcp_tools = []
        
        # Registrar las herramientas disponibles con sus funciones handler
        self._register_tools()
        
    def _register_tools(self):
        """Registra las herramientas de Azure DevOps con sus handlers correspondientes"""
        self.tools = {
            "list_repositories": list_repositories_handler,
            "get_work_item": get_work_item_handler,
            "list_work_items": list_work_items_handler,
            "list_recent_work_items": list_recent_work_items_handler,
            "list_pipelines": list_pipelines_handler,
            "list_available_tools": list_available_tools_handler
        }
        
    async def get_all_tools(self):
        """
        Obtiene todas las herramientas disponibles (MCP base + personalizadas)
        siguiendo el enfoque recomendado por el blog y la API oficial de MCP.
        
        Returns:
            Lista de herramientas combinadas
        """
        # Configurar los parámetros del servidor MCP
        self.server_params = StdioServerParams(
            command=self.command.split()[0],  # python
            args=self.command.split()[1:],    # ["-m", "mcp.server"]
        )
        
        # Obtener herramientas base MCP usando la API oficial
        print("Obteniendo herramientas MCP disponibles...")
        try:
            self.mcp_tools = await mcp_server_tools(self.server_params)
            print(f"Se encontraron {len(self.mcp_tools)} herramientas MCP base")
        except Exception as e:
            print(f"Error al obtener herramientas MCP: {str(e)}")
            self.mcp_tools = []
        
        # Convertir las herramientas personalizadas al formato esperado por Autogen
        azdo_tool = AzureDevOpsTool()
        custom_tools = []
        
        for tool_name, handler in self.tools.items():
            # Define una función wrapper para el handler
            async def execute_handler(params, tool_handler=handler):
                # Crear una instancia fresca para cada ejecución
                azdo_tool_instance = AzureDevOpsTool()
                return await tool_handler(azdo_tool_instance, params)
            
            # Crear el objeto de herramienta en el formato esperado por Autogen
            custom_tool = {
                "name": tool_name,
                "description": f"Azure DevOps Tool: {tool_name}",
                "execute": execute_handler
            }
            custom_tools.append(custom_tool)
        
        # Registrar herramientas con MCP (informativo)
        # Creamos una estructura dummy para pasar como mcp_tool ya que
        # la verdadera integración ocurre a través de mcp_server_tools
        dummy_mcp_tool = {"name": "dummy_tool"}
        azdo_tools_config = register_azdo_tools_with_mcp(dummy_mcp_tool)
        print(f"Registradas herramientas de Azure DevOps con MCP")
        
        # Combinar con las herramientas MCP base
        all_tools = self.mcp_tools + custom_tools
        return all_tools

    async def handle_request(self, request):
        """
        Maneja una solicitud para una herramienta MCP
        
        Args:
            request: Solicitud MCP con herramienta y argumentos
        
        Returns:
            Resultado de la ejecución de la herramienta
        """
        try:
            # Extraer nombre de la herramienta y argumentos
            tool_name = request.get("name")
            arguments = request.get("arguments", {})
            
            # Verificar si la herramienta existe
            if tool_name not in self.tools:
                return {"status": "error", "message": f"Herramienta '{tool_name}' no encontrada"}
            
            # Obtener el handler
            handler = self.tools[tool_name]
            
            # Crear una instancia de AzureDevOpsTool para el handler
            azdo_tool = AzureDevOpsTool()
            
            # Ejecutar el handler con los argumentos
            result = await handler(azdo_tool, arguments)
            return result
            
        except Exception as e:
            return {"status": "error", "message": f"Error al ejecutar la herramienta: {str(e)}"}
        
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