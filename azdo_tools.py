import os
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv
import base64
from dateutil import parser as date_parser
from datetime import datetime, timedelta
import re

# Cargar variables de entorno
load_dotenv()

def register_azdo_tools_with_mcp():
    """
    Registra las herramientas de Azure DevOps con el servidor MCP.
    Esta función es llamada por el cliente MCP para registrar las funcionalidades
    de interacción con Azure DevOps.
    
    Returns:
        List: Lista de herramientas registradas
    """
    # Crear lista de herramientas disponibles para registro MCP
    available_tools = [
        {
            "name": "list_repositories",
            "description": "Listar repositorios en Azure DevOps",
        },
        {
            "name": "list_work_items",
            "description": "Listar work items en Azure DevOps con filtrado por tipo, fecha y estado",
        },
        {
            "name": "list_pipelines",
            "description": "Listar pipelines en Azure DevOps",
        },
        {
            "name": "filter_by_date",
            "description": "Filtrar recursos por fecha usando lenguaje natural",
        }
    ]
    
    print("Registrando herramientas de Azure DevOps con el servidor MCP:")
    for tool in available_tools:
        print(f"  - {tool['name']}: {tool['description']}")
        
    return available_tools

def list_available_tools():
    """
    Devuelve una lista de las herramientas disponibles en la clase AzureDevOpsTool
    
    Returns:
        List[Dict]: Lista de diccionarios con nombre y descripción de cada herramienta
    """
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
            "name": "search_work_items_by_type_and_date",
            "description": "Búsqueda especializada de work items filtrando por tipo y fecha"
        },
        {
            "name": "parse_natural_language_date",
            "description": "Convierte expresiones de fecha en lenguaje natural a rangos de fechas específicos"
        }
    ]
    return tools

class AzureDevOpsTool:
    """Clase para interactuar con Azure DevOps API utilizando PAT (simplificada para operaciones de items)"""
    
    def __init__(self):
        """Inicializar con credenciales desde variables de entorno"""
        self.pat = os.environ.get("AZDO_PAT")
        self.organization = os.environ.get("AZDO_ORG")
        self.project = os.environ.get("AZDO_PROJECT", "")  # Ahora es opcional
        
        if not all([self.pat, self.organization]):
            raise ValueError("Faltan credenciales de Azure DevOps en el archivo .env (AZDO_PAT, AZDO_ORG son obligatorios)")
        
        # Crear headers de autenticación
        self.headers = {
            'Authorization': f'Basic {self._get_auth_token()}',
            'Content-Type': 'application/json'
        }
    
    def _get_auth_token(self) -> str:
        """Crear token de autenticación Basic para Azure DevOps API"""
        token = f":{self.pat}"
        encoded_bytes = base64.b64encode(token.encode("utf-8"))
        return encoded_bytes.decode("utf-8")

    # ==== HELPER METHODS ====
    def _parse_date_filter(self, date_filter):
        """
        Parse natural language date filters into a date range.
        
        Args:
            date_filter (str): Natural language date filter like 'today', 'yesterday', 'last week', etc.
            
        Returns:
            tuple: (from_date, to_date) in YYYY-MM-DD format
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_filter = date_filter.lower().strip()
        
        # Basic date filters
        if date_filter == 'today':
            return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif date_filter == 'yesterday':
            yesterday = today - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')
        elif date_filter == 'this week':
            start_of_week = today - timedelta(days=today.weekday())
            return start_of_week.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif date_filter == 'last week':
            end_of_last_week = today - timedelta(days=today.weekday() + 1)
            start_of_last_week = end_of_last_week - timedelta(days=6)
            return start_of_last_week.strftime('%Y-%m-%d'), end_of_last_week.strftime('%Y-%m-%d')
        elif date_filter == 'this month':
            start_of_month = today.replace(day=1)
            return start_of_month.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif date_filter == 'last month':
            end_of_last_month = today.replace(day=1) - timedelta(days=1)
            start_of_last_month = end_of_last_month.replace(day=1)
            return start_of_last_month.strftime('%Y-%m-%d'), end_of_last_month.strftime('%Y-%m-%d')
        elif date_filter == 'this year':
            start_of_year = today.replace(month=1, day=1)
            return start_of_year.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
        elif date_filter == 'last year':
            last_year = today.year - 1
            start_of_last_year = today.replace(year=last_year, month=1, day=1)
            end_of_last_year = today.replace(year=last_year, month=12, day=31)
            return start_of_last_year.strftime('%Y-%m-%d'), end_of_last_year.strftime('%Y-%m-%d')
            
        # More complex patterns with regex
        
        # Handle "last X days"
        last_n_days_match = re.match(r'last (\d+) days?', date_filter)
        if last_n_days_match:
            days = int(last_n_days_match.group(1))
            from_date = today - timedelta(days=days)
            return from_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
            
        # Handle "last X weeks"
        last_n_weeks_match = re.match(r'last (\d+) weeks?', date_filter)
        if last_n_weeks_match:
            weeks = int(last_n_weeks_match.group(1))
            from_date = today - timedelta(weeks=weeks)
            return from_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
            
        # Handle "last X months"
        last_n_months_match = re.match(r'last (\d+) months?', date_filter)
        if last_n_months_match:
            months = int(last_n_months_match.group(1))
            # Calculate date by going back months
            year = today.year
            month = today.month - months
            
            # Adjust if we crossed a year boundary
            while month <= 0:
                month += 12
                year -= 1
                
            from_date = today.replace(year=year, month=month)
            return from_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
            
        # Handle specific date ranges with format "YYYY-MM-DD to YYYY-MM-DD"
        date_range_match = re.match(r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})', date_filter)
        if date_range_match:
            from_date = date_range_match.group(1)
            to_date = date_range_match.group(2)
            return from_date, to_date
            
        # Handle specific dates with format "YYYY-MM-DD"
        specific_date_match = re.match(r'(\d{4}-\d{2}-\d{2})', date_filter)
        if specific_date_match:
            specific_date = specific_date_match.group(1)
            return specific_date, specific_date
            
        # Handle "since YYYY-MM-DD"
        since_date_match = re.match(r'since\s+(\d{4}-\d{2}-\d{2})', date_filter)
        if since_date_match:
            from_date = since_date_match.group(1)
            return from_date, today.strftime('%Y-%m-%d')
            
        # Handle "before YYYY-MM-DD"
        before_date_match = re.match(r'before\s+(\d{4}-\d{2}-\d{2})', date_filter)
        if before_date_match:
            to_date = before_date_match.group(1)
            # Use a reasonably old date as the start date
            from_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
            return from_date, to_date
            
        # Default to last 30 days if no match
        default_from = today - timedelta(days=30)
        return default_from.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
    
    def _filter_by_date(self, items: List[Dict], date_field: str, date_filter: str) -> List[Dict]:
        """
        Filtra una lista de items por un campo de fecha según un filtro en lenguaje natural.
        
        Args:
            items (List[Dict]): Lista de items a filtrar
            date_field (str): Campo que contiene la fecha en el item
            date_filter (str): Filtro en formato natural como "2025", "enero 2025", etc.
            
        Returns:
            List[Dict]: Items filtrados
        """
        from_date, to_date = self._parse_date_filter(date_filter)
        if not from_date and not to_date:
            return items
            
        filtered_items = []
        
        for item in items:
            # Manejar estructuras anidadas con notación de punto
            if "." in date_field:
                parts = date_field.split(".")
                value = item
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
                item_date_str = value
            else:
                item_date_str = item.get(date_field)
                
            if not item_date_str:
                continue
                
            try:
                item_date = date_parser.parse(item_date_str)
                
                from_date_obj = date_parser.parse(from_date) if from_date else None
                to_date_obj = date_parser.parse(to_date) if to_date else None
                
                if from_date_obj and to_date_obj:
                    if from_date_obj <= item_date <= to_date_obj:
                        filtered_items.append(item)
                elif from_date_obj:
                    if item_date >= from_date_obj:
                        filtered_items.append(item)
                elif to_date_obj:
                    if item_date <= to_date_obj:
                        filtered_items.append(item)
            except:
                # Si hay error en el parseo de fechas, simplemente no incluir el item
                pass
                
        return filtered_items
    
    # ==== REPOSITORY TOOLS ====
    def list_repositories(self, project: Optional[str] = None, date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista los repositorios en un proyecto de Azure DevOps
        
        Args:
            project: Nombre del proyecto de Azure DevOps (opcional, usa el predeterminado si no se proporciona)
            date_filter: Filtro de fecha en lenguaje natural (ej. "2025", "enero 2025")
            
        Returns:
            Lista de repositorios
        """
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para listar repositorios")
            
        url = f"{self.organization}/{project_to_use}/_apis/git/repositories?api-version=7.0"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            repositories = response.json().get('value', [])
            
            # Aplicar filtro de fecha si se proporciona
            if date_filter:
                return self._filter_by_date(repositories, "createdDate", date_filter)
            
            return repositories
        except Exception as e:
            print(f"Error al listar repositorios: {str(e)}")
            return []
    
    # ==== PIPELINE TOOLS ====
    def list_pipelines(self, project: Optional[str] = None, date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lista los pipelines en un proyecto de Azure DevOps
        
        Args:
            project: Nombre del proyecto de Azure DevOps (opcional, usa el predeterminado si no se proporciona)
            date_filter: Filtro de fecha en lenguaje natural (ej. "2025", "enero 2025")
            
        Returns:
            Lista de pipelines
        """
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para listar pipelines")
            
        url = f"{self.organization}/{project_to_use}/_apis/pipelines?api-version=7.0"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            pipelines = response.json().get('value', [])
            
            # Aplicar filtro de fecha si se proporciona
            if date_filter:
                return self._filter_by_date(pipelines, "createdDate", date_filter)
            
            return pipelines
        except Exception as e:
            print(f"Error al listar pipelines: {str(e)}")
            return []
    
    # ==== WORK ITEM TOOLS ====
    def get_work_item(self, work_item_id: int, project: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener un work item por ID
        
        Args:
            work_item_id: ID del work item a obtener
            project: Nombre del proyecto de Azure DevOps (opcional, usa el predeterminado si no se proporciona)
            
        Returns:
            Detalles del work item o diccionario vacío si no se encuentra
        """
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para obtener work items")
            
        url = f"{self.organization}/{project_to_use}/_apis/wit/workitems/{work_item_id}?$expand=all&api-version=7.0"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            # Si el work item no existe, devolver un mensaje claro
            if response.status_code == 404:
                print(f"Work item con ID {work_item_id} no encontrado")
                return {"error": f"Work item con ID {work_item_id} no encontrado"}
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener work item {work_item_id}: {str(e)}")
            return {"error": f"Error al obtener work item {work_item_id}: {str(e)}"}
    
    def list_work_items(self, query_string: str = None, project: Optional[str] = None, work_item_type: Optional[str] = None, date_filter: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Ejecutar una consulta WIQL para obtener work items con diversos filtros
        
        Args:
            query_string: Consulta WIQL personalizada (si se proporciona, ignora otros filtros)
            project: Proyecto de Azure DevOps
            work_item_type: Tipo de work item (Epic, User Story, Task, Bug, etc.)
            date_filter: Filtro de fecha en lenguaje natural (ej. "2025", "enero 2025")
            state: Estado del work item (Active, Closed, etc.)
            
        Returns:
            Lista de work items
        """
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para listar work items")
        
        # Determinar si podemos aplicar el filtro de fecha en la consulta WIQL (server-side)
        date_filter_wiql = ""
        client_side_date_filter = None
        
        if date_filter and not query_string:
            from_date, to_date = self._parse_date_filter(date_filter)
            
            if from_date and to_date:
                # Si tenemos ambas fechas, podemos aplicar server-side
                date_filter_wiql = f"AND [System.CreatedDate] >= '{from_date}' AND [System.CreatedDate] <= '{to_date}'"
                # No necesitamos filtrado adicional client-side
            elif from_date:
                # Solo tenemos fecha inicial
                date_filter_wiql = f"AND [System.CreatedDate] >= '{from_date}'"
                # No necesitamos filtrado adicional client-side
            elif to_date:
                # Solo tenemos fecha final
                date_filter_wiql = f"AND [System.CreatedDate] <= '{to_date}'"
                # No necesitamos filtrado adicional client-side
            else:
                # No pudimos convertir el filtro a fechas, usaremos client-side filtering
                client_side_date_filter = date_filter
        elif date_filter and query_string:
            # Si hay query_string personalizada, usaremos client-side filtering
            client_side_date_filter = date_filter
            
        # Si no hay query_string personalizada, construir una según los filtros
        if not query_string:
            # Iniciar con la base de la consulta
            base_query = f"SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType], [System.CreatedDate], [System.ChangedDate], [System.AssignedTo], [System.Tags] FROM WorkItems WHERE [System.TeamProject] = '{project_to_use}'"
            
            # Añadir filtros según se proporcionen
            filters = []
            
            if work_item_type:
                filters.append(f"[System.WorkItemType] = '{work_item_type}'")
                
            if state:
                filters.append(f"[System.State] = '{state}'")
                
            # Combinar filtros si existen
            if filters:
                base_query += " AND " + " AND ".join(filters)
                
            # Añadir filtro de fecha si existe
            if date_filter_wiql:
                base_query += " " + date_filter_wiql
                
            # Ordenar por fecha de creación descendente
            base_query += " ORDER BY [System.CreatedDate] DESC"
            
            query_string = base_query
            
        url = f"{self.organization}/{project_to_use}/_apis/wit/wiql?api-version=7.0"
        data = {"query": query_string}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        
        # Obtener los IDs de los work items
        work_item_ids = [wi['id'] for wi in response.json().get('workItems', [])]
        
        if not work_item_ids:
            return []
        
        # Obtener detalles de los work items
        details = []
        batch_size = 200  # Azure DevOps API limita el número de IDs por solicitud
        
        for i in range(0, len(work_item_ids), batch_size):
            batch = work_item_ids[i:i + batch_size]
            ids_str = ','.join(map(str, batch))
            details_url = f"{self.organization}/{project_to_use}/_apis/wit/workitems?ids={ids_str}&api-version=7.0&$expand=all"
            details_response = requests.get(details_url, headers=self.headers)
            details_response.raise_for_status()
            details.extend(details_response.json().get('value', []))
        
        # Si hay un filtro de fecha que no pudimos aplicar server-side, aplicarlo client-side
        if client_side_date_filter:
            # Filtrar por fecha de creación
            return self._filter_by_date(details, "fields.System.CreatedDate", client_side_date_filter)
            
        return details
    
    def search_work_items_by_type_and_date(self, work_item_type: str, date_filter: str, project: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Búsqueda especializada de work items por tipo y fecha
        
        Args:
            work_item_type: Tipo de work item (Epic, User Story, Task, Bug, etc.)
            date_filter: Filtro de fecha en lenguaje natural (ej. "2025", "enero 2025")
            project: Proyecto de Azure DevOps
            state: Estado del work item (Active, Closed, etc.)
            
        Returns:
            Lista de work items que coinciden con los criterios
        """
        return self.list_work_items(
            query_string=None,
            project=project,
            work_item_type=work_item_type,
            date_filter=date_filter,
            state=state
        )