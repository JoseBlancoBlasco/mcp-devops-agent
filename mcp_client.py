import os
from typing import List, Dict, Any, Optional
import time
from dotenv import load_dotenv
from azdo_tools import AzureDevOpsTool, register_azdo_tools_with_mcp

# Cargar variables de entorno
load_dotenv()

class DevOpsMCPClient:
    def __init__(self, command="python -m mcp.server"):
        """
        Inicializar el cliente MCP para DevOps
        
        Args:
            command: Comando para iniciar el servidor MCP (como string)
        """
        self.command = command
        self.is_initialized = False
        self.azdo_tool = None
        self.mcp_tool = None
        
    def initialize(self):
        """
        Inicializar el cliente MCP y las herramientas de Azure DevOps
        """
        try:
            # Inicializar la herramienta de Azure DevOps
            self.azdo_tool = AzureDevOpsTool()
            print(f"Herramienta Azure DevOps inicializada. Organización: {self.azdo_tool.organization}")
            if self.azdo_tool.project:
                print(f"Proyecto por defecto: {self.azdo_tool.project}")
                
            # Marcamos el cliente como inicializado
            self.is_initialized = True
            print(f"Cliente MCP inicializado")
            
        except Exception as e:
            print(f"Error al inicializar cliente MCP: {str(e)}")
        
    def register_to_agent(self, agent):
        """
        Registrar capacidades MCP con un agente AutoGen.
        """
        if not self.is_initialized:
            self.initialize()
            
        print(f"Registrando capacidades MCP al agente '{agent.name}'...")
        
        # Verificar si el agente tiene el atributo 'tools'
        if hasattr(agent, "tools"):
            # Si ya tiene herramientas definidas, mantenemos una referencia
            current_tools = agent.tools if agent.tools else []
            
            # Aquí podríamos añadir más configuraciones si son necesarias
            # En este punto, el agente ya está configurado para usar el servidor MCP
            
            print(f"El agente '{agent.name}' ahora puede usar el servidor MCP")
        else:
            print(f"¡Advertencia! El agente {agent.name} no tiene atributo 'tools'. Asegúrate de usar la versión correcta de autogen.")
            
    def register_custom_tools(self):
        """
        Registrar herramientas personalizadas de Azure DevOps con el cliente MCP
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            from azdo_tools import list_available_tools, register_azdo_tools_with_mcp
            
            # Registrar las herramientas con MCP
            registered_tools = register_azdo_tools_with_mcp()
            
            # Obtener y mostrar las herramientas disponibles
            available_tools = list_available_tools()
            print("\nHerramientas de Azure DevOps disponibles:")
            for tool in available_tools:
                print(f"  - {tool['name']}: {tool['description']}")
                
            return registered_tools
            
        except Exception as e:
            print(f"Error al registrar herramientas personalizadas: {str(e)}")
            
        return []
    
    # === Métodos de ayuda para acceder a Azure DevOps ===
    
    def get_work_item(self, work_item_id, project=None):
        """
        Obtener detalles de un work item específico por su ID
        
        Args:
            work_item_id: ID del work item a obtener
            project: Proyecto de Azure DevOps (opcional)
            
        Returns:
            Diccionario con los detalles del work item o mensaje de error
        """
        if not self.azdo_tool:
            print("Cliente Azure DevOps no inicializado")
            return {"error": "Cliente Azure DevOps no inicializado"}
        
        try:
            return self.azdo_tool.get_work_item(work_item_id, project)
        except Exception as e:
            print(f"Error al obtener work item {work_item_id}: {str(e)}")
            return {"error": f"Error al obtener work item {work_item_id}: {str(e)}"}
    
    def list_repositories(self, project=None, date_filter=None):
        """
        Listar repositorios en un proyecto con opción de filtrado por fecha
        
        Args:
            project: Proyecto de Azure DevOps (opcional)
            date_filter: Filtro de fecha en lenguaje natural (ej. "2025", "enero 2025")
        
        Returns:
            Lista de repositorios filtrados
        """
        if not self.azdo_tool:
            print("Cliente Azure DevOps no inicializado")
            return []
        
        try:
            return self.azdo_tool.list_repositories(project, date_filter)
        except Exception as e:
            print(f"Error al listar repositorios: {str(e)}")
            return []
    
    def list_work_items(self, query=None, project=None, work_item_type=None, date_filter=None, state=None):
        """
        Listar work items con múltiples opciones de filtrado
        
        Args:
            query: Consulta WIQL personalizada (opcional)
            project: Proyecto de Azure DevOps (opcional)
            work_item_type: Tipo de work item (Epic, User Story, Task, Bug, etc.) (opcional)
            date_filter: Filtro de fecha en lenguaje natural (ej. "2025", "enero 2025") (opcional)
            state: Estado del work item (Active, Closed, etc.) (opcional)
            
        Returns:
            Lista de work items que coinciden con los criterios
        """
        if not self.azdo_tool:
            print("Cliente Azure DevOps no inicializado")
            return []
        
        try:
            return self.azdo_tool.list_work_items(query, project, work_item_type, date_filter, state)
        except Exception as e:
            print(f"Error al listar work items: {str(e)}")
            return []
    
    def list_pipelines(self, project=None, date_filter=None):
        """
        Listar pipelines en un proyecto con opción de filtrado por fecha
        
        Args:
            project: Proyecto de Azure DevOps (opcional)
            date_filter: Filtro de fecha en lenguaje natural (opcional)
            
        Returns:
            Lista de pipelines filtrados
        """
        if not self.azdo_tool:
            print("Cliente Azure DevOps no inicializado")
            return []
        
        try:
            return self.azdo_tool.list_pipelines(project, date_filter)
        except Exception as e:
            print(f"Error al listar pipelines: {str(e)}")
            return []
    
    # === Nuevos métodos especializados para filtrado por fecha ===
    
    def get_repositories_by_date(self, date_filter, project=None):
        """
        Obtener repositorios creados en una fecha específica
        
        Args:
            date_filter: Filtro de fecha en formato natural (ej. "2025", "enero 2025")
            project: Proyecto de Azure DevOps (opcional)
            
        Returns:
            Lista de repositorios que coinciden con el filtro de fecha
        """
        return self.list_repositories(project, date_filter)
    
    def get_work_items_by_type_and_date(self, work_item_type, date_filter, project=None, state=None):
        """
        Buscar work items por tipo y fecha
        
        Args:
            work_item_type: Tipo de work item (Epic, User Story, Task, Bug, etc.)
            date_filter: Filtro de fecha en formato natural (ej. "2025", "enero 2025")
            project: Proyecto de Azure DevOps (opcional)
            state: Estado del work item (opcional)
            
        Returns:
            Lista de work items que coinciden con los criterios
        """
        return self.azdo_tool.search_work_items_by_type_and_date(
            work_item_type=work_item_type,
            date_filter=date_filter,
            project=project,
            state=state
        )
    
    def get_pipelines_by_date(self, date_filter, project=None):
        """
        Obtener pipelines creados o actualizados en una fecha específica
        
        Args:
            date_filter: Filtro de fecha en formato natural (ej. "2025", "enero 2025")
            project: Proyecto de Azure DevOps (opcional)
            
        Returns:
            Lista de pipelines que coinciden con el filtro de fecha
        """
        return self.list_pipelines(project, date_filter)

    def parse_natural_query(self, query_text):
        """
        Parsea una consulta en lenguaje natural e intenta convertirla en llamadas a métodos
        
        Args:
            query_text: Texto de la consulta en lenguaje natural
            
        Returns:
            Resultado de la consulta o mensaje de error
        """
        query_text = query_text.lower().strip()
        
        # Detectar año u otro filtro de fecha
        date_filter = None
        
        # Buscar año como 4 dígitos (ejemplo: "2025")
        for word in query_text.split():
            if word.isdigit() and len(word) == 4:
                date_filter = word
                break
        
        # Buscar meses del año
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        for month in months:
            if month in query_text:
                # Intentar encontrar un año cercano al mes
                words = query_text.split()
                month_index = words.index(month) if month in words else -1
                
                if month_index >= 0:
                    # Buscar un año antes o después del mes
                    year = None
                    for i in range(max(0, month_index-2), min(len(words), month_index+3)):
                        if words[i].isdigit() and len(words[i]) == 4:
                            year = words[i]
                            break
                    
                    if year:
                        date_filter = f"{month} {year}"
                    else:
                        # Si no hay año específico, usar el año actual
                        import datetime
                        current_year = datetime.datetime.now().year
                        date_filter = f"{month} {current_year}"
                break
        
        # Consultas para repositorios
        if any(keyword in query_text for keyword in ["repositorios", "repos", "repositories"]):
            if date_filter:
                return self.get_repositories_by_date(date_filter)
            else:
                return self.list_repositories()
        
        # Consultas para work items
        elif any(keyword in query_text for keyword in ["work items", "tareas", "epics", "historias", "bugs"]):
            work_item_type = None
            
            # Detectar tipo de work item
            if "epic" in query_text or "epics" in query_text:
                work_item_type = "Epic"
            elif "historia" in query_text or "user story" in query_text or "historias" in query_text:
                work_item_type = "User Story"
            elif "tarea" in query_text or "task" in query_text or "tareas" in query_text:
                work_item_type = "Task"
            elif "bug" in query_text or "bugs" in query_text:
                work_item_type = "Bug"
            
            # Detectar estado
            state = None
            if "activ" in query_text:  # para "activo", "activas", etc.
                state = "Active"
            elif "cerrad" in query_text or "completad" in query_text:  # para "cerrado", "completado", etc.
                state = "Closed"
            
            if work_item_type and date_filter:
                return self.get_work_items_by_type_and_date(work_item_type, date_filter, state=state)
            elif work_item_type:
                return self.list_work_items(work_item_type=work_item_type, state=state)
            elif date_filter:
                return self.list_work_items(date_filter=date_filter, state=state)
            else:
                return self.list_work_items()
        
        # Consultas para pipelines
        elif any(keyword in query_text for keyword in ["pipeline", "pipelines", "ci/cd"]):
            if date_filter:
                return self.get_pipelines_by_date(date_filter)
            else:
                return self.list_pipelines()
        
        # Si no encaja en ninguna categoría
        return {"error": "No se pudo interpretar la consulta. Por favor, intenta con otro formato."}

if __name__ == "__main__":
    # Demo simple del cliente MCP
    client = DevOpsMCPClient()
    client.initialize()
    print("Ejecuta main.py para iniciar el agente con capacidades MCP")