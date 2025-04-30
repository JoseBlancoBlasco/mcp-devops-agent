import os
from typing import List, Dict, Any, Optional, Union
import requests
from dotenv import load_dotenv
import base64
import json
import datetime
from dateutil import parser as date_parser
from datetime import datetime, timedelta
from typing import Tuple

# Cargar variables de entorno
load_dotenv()

class AzureDevOpsTool:
    """Clase para interactuar con Azure DevOps API utilizando PAT"""
    
    def __init__(self):
        """Inicializar con credenciales desde variables de entorno"""
        self.pat = os.environ.get("AZDO_PAT")
        self.organization = os.environ.get("AZDO_ORG")
        self.project = os.environ.get("AZDO_PROJECT", "")  # Ahora es opcional
        self.repo = os.environ.get("AZDO_REPO", "")  # Ahora es opcional
        
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
        from datetime import datetime, timedelta
        
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
        import re
        
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
    
    # ==== USER TOOLS ====
    def get_me(self) -> Dict[str, Any]:
        """Obtener información del usuario autenticado"""
        url = f"{self.organization}/_apis/graph/me?api-version=7.0"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    # ==== ORGANIZATION TOOLS ====
    def list_organizations(self) -> List[Dict[str, Any]]:
        """Listar todas las organizaciones accesibles"""
        # Como estamos usando PAT y ya tenemos una organización configurada, devolvemos esa
        # En un entorno real con Azure CLI auth se podría listar todas las orgs
        return [{"name": self.organization.split('/')[-2], "url": self.organization}]
    
    # ==== PROJECT TOOLS ====
    def list_projects(self) -> List[Dict[str, Any]]:
        """Listar todos los proyectos en una organización"""
        url = f"{self.organization}/_apis/projects?api-version=7.0"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('value', [])
    
    def get_project(self, project: str) -> Dict[str, Any]:
        """Obtener detalles de un proyecto específico"""
        url = f"{self.organization}/_apis/projects/{project}?api-version=7.0"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_project_details(self, project: str) -> Dict[str, Any]:
        """Obtener detalles completos de un proyecto incluyendo proceso, tipos de work items y equipos"""
        # Básico del proyecto
        project_info = self.get_project(project)
        
        # Tipos de work items
        wit_url = f"{self.organization}/{project}/_apis/wit/workitemtypes?api-version=7.0"
        wit_response = requests.get(wit_url, headers=self.headers)
        wit_response.raise_for_status()
        
        # Equipos
        teams_url = f"{self.organization}/_apis/projects/{project}/teams?api-version=7.0"
        teams_response = requests.get(teams_url, headers=self.headers)
        teams_response.raise_for_status()
        
        # Combinar toda la información
        combined_info = {
            "project": project_info,
            "workItemTypes": wit_response.json().get('value', []),
            "teams": teams_response.json().get('value', [])
        }
        
        return combined_info
    
    # ==== REPOSITORY TOOLS ====
    def list_repositories(self, project: Optional[str] = None, date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar los repositorios disponibles en el proyecto
        
        Args:
            project: Nombre del proyecto
            date_filter: Filtro de fecha en lenguaje natural (ej. "2025", "enero 2025")
            
        Returns:
            Lista de repositorios filtrados
        """
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para listar repositorios")
            
        url = f"{self.organization}/{project_to_use}/_apis/git/repositories?api-version=7.0"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        repos = response.json().get('value', [])
        
        # Si hay un filtro de fecha, aplicarlo
        if date_filter:
            # Para cada repo, obtener información más detallada incluyendo fecha de creación
            detailed_repos = []
            for repo in repos:
                try:
                    repo_id = repo.get('id')
                    repo_url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repo_id}?api-version=7.0"
                    repo_response = requests.get(repo_url, headers=self.headers)
                    if repo_response.status_code == 200:
                        detailed_repos.append(repo_response.json())
                    else:
                        detailed_repos.append(repo)  # Fallback to basic info
                except Exception:
                    detailed_repos.append(repo)  # Fallback to basic info
            
            # Filtrar por fecha de creación
            return self._filter_by_date(detailed_repos, "createdDate", date_filter)
            
        return repos
    
    def get_repository(self, repository_id: str, project: Optional[str] = None) -> Dict[str, Any]:
        """Obtener detalles de un repositorio específico"""
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para obtener un repositorio")
            
        url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}?api-version=7.0"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_repository_details(self, repository_id: str, project: Optional[str] = None) -> Dict[str, Any]:
        """Obtener información detallada sobre un repositorio incluyendo estadísticas y referencias"""
        repo_info = self.get_repository(repository_id, project)
        
        # Obtener refs (ramas, tags)
        project_to_use = project or self.project
        refs_url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/refs?api-version=7.0"
        refs_response = requests.get(refs_url, headers=self.headers)
        refs_response.raise_for_status()
        
        # Estadísticas básicas
        stats_url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/stats/branches?api-version=7.0"
        stats_response = requests.get(stats_url, headers=self.headers)
        stats_info = []
        if stats_response.status_code == 200:
            stats_info = stats_response.json().get('value', [])
        
        # Combinar toda la información
        combined_info = {
            "repository": repo_info,
            "refs": refs_response.json().get('value', []),
            "stats": stats_info
        }
        
        return combined_info
    
    def get_file_content(self, repository_id: str, path: str, branch: str = "main", project: Optional[str] = None) -> Union[Dict[str, Any], str]:
        """Obtener contenido de un archivo o directorio de un repositorio"""
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para obtener contenido de archivos")
            
        # Primero obtener el item para determinar si es archivo o directorio
        item_url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/items?path={path}&versionDescriptor.version={branch}&api-version=7.0"
        item_response = requests.get(item_url, headers=self.headers)
        item_response.raise_for_status()
        
        # Si es directorio, devolver lista de items
        if "isFolder" in item_response.json() and item_response.json()["isFolder"]:
            items_url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/items?path={path}&versionDescriptor.version={branch}&recursionLevel=OneLevel&api-version=7.0"
            items_response = requests.get(items_url, headers=self.headers)
            items_response.raise_for_status()
            return items_response.json()
        
        # Si es archivo, obtener su contenido como texto
        content_url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/items?path={path}&versionDescriptor.version={branch}&download=true&api-version=7.0"
        content_response = requests.get(content_url, headers=self.headers)
        content_response.raise_for_status()
        return content_response.text
    
    # ==== WORK ITEM TOOLS ====
    def get_work_item(self, work_item_id: int, project: Optional[str] = None) -> Dict[str, Any]:
        """Obtener un work item por ID"""
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para obtener work items")
            
        url = f"{self.organization}/{project_to_use}/_apis/wit/workitems/{work_item_id}?$expand=all&api-version=7.0"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
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
    
    # ==== PIPELINES TOOLS ====
    def list_pipelines(self, project: Optional[str] = None, date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar pipelines disponibles en el proyecto
        
        Args:
            project: Nombre del proyecto
            date_filter: Filtro de fecha en lenguaje natural
            
        Returns:
            Lista de pipelines filtrados
        """
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para listar pipelines")
            
        url = f"{self.organization}/{project_to_use}/_apis/pipelines?api-version=7.0"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        pipelines = response.json().get('value', [])
        
        # Si hay un filtro de fecha, aplicarlo
        if date_filter:
            # Para cada pipeline, obtener información detallada incluyendo historial
            detailed_pipelines = []
            for pipeline in pipelines:
                try:
                    pipeline_id = pipeline.get('id')
                    runs_url = f"{self.organization}/{project_to_use}/_apis/pipelines/{pipeline_id}/runs?api-version=7.0"
                    runs_response = requests.get(runs_url, headers=self.headers)
                    if runs_response.status_code == 200:
                        runs = runs_response.json().get('value', [])
                        if runs:
                            # Añadir el run más reciente al pipeline
                            pipeline['latestRun'] = runs[0]
                    detailed_pipelines.append(pipeline)
                except Exception:
                    detailed_pipelines.append(pipeline)
            
            # Filtrar por fecha de creación del pipeline o fecha del último run
            return self._filter_by_date(detailed_pipelines, "latestRun.createdDate", date_filter)
            
        return pipelines
    
    # ==== PULL REQUEST TOOLS ====
    def create_pull_request(self, 
                           source_branch: str, 
                           target_branch: str, 
                           title: str, 
                           description: str,
                           repository_id: str,
                           project: Optional[str] = None) -> Dict[str, Any]:
        """Crear un nuevo pull request entre ramas en un repositorio"""
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para crear un pull request")
            
        url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/pullrequests?api-version=7.0"
        
        payload = {
            "sourceRefName": f"refs/heads/{source_branch}",
            "targetRefName": f"refs/heads/{target_branch}",
            "title": title,
            "description": description
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_pull_requests(self, 
                          repository_id: Optional[str] = None, 
                          status: str = "active", 
                          project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Listar y filtrar pull requests en un proyecto o repositorio"""
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para listar pull requests")
        
        # Construir URL según tengamos repositorio o no
        if repository_id:
            url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/pullrequests?searchCriteria.status={status}&api-version=7.0"
        else:
            url = f"{self.organization}/{project_to_use}/_apis/git/pullrequests?searchCriteria.status={status}&api-version=7.0"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('value', [])
    
    def get_pull_request_comments(self, pull_request_id: int, repository_id: str, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener comentarios y hilos de comentarios de un pull request específico"""
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para obtener comentarios de pull requests")
            
        url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/pullRequests/{pull_request_id}/threads?api-version=7.0"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('value', [])
    
    def add_pull_request_comment(self, 
                               pull_request_id: int, 
                               repository_id: str, 
                               comment: str, 
                               thread_id: Optional[int] = None,
                               project: Optional[str] = None) -> Dict[str, Any]:
        """Añadir un comentario a un pull request (responder a comentarios existentes o crear nuevos hilos)"""
        project_to_use = project or self.project
        if not project_to_use:
            raise ValueError("Se requiere un proyecto para añadir comentarios a pull requests")
        
        # Si no hay thread_id, crear un nuevo hilo
        if thread_id is None:
            # Crear un nuevo hilo
            thread_url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/pullRequests/{pull_request_id}/threads?api-version=7.0"
            thread_payload = {
                "comments": [{
                    "content": comment
                }]
            }
            response = requests.post(thread_url, headers=self.headers, json=thread_payload)
        else:
            # Añadir a hilo existente
            comment_url = f"{self.organization}/{project_to_use}/_apis/git/repositories/{repository_id}/pullRequests/{pull_request_id}/threads/{thread_id}/comments?api-version=7.0"
            comment_payload = {
                "content": comment
            }
            response = requests.post(comment_url, headers=self.headers, json=comment_payload)
        
        response.raise_for_status()
        return response.json()

# Funciones para registrar con MCP
def register_azdo_tools_with_mcp(mcp_tool, tool_idx=0):
    """
    Registrar herramientas Azure DevOps con una herramienta MCP
    
    Args:
        mcp_tool: Una herramienta MCP (StdioMcpToolAdapter o similar)
        tool_idx: Índice de la herramienta (solo informativo)
        
    Returns:
        La herramienta MCP modificada o None si hubo un error
    """
    try:
        azdo = AzureDevOpsTool()
        print(f"Registrando herramientas de Azure DevOps con adaptador MCP #{tool_idx}")
        
        # En la nueva implementación, no registramos herramientas directamente con el cliente
        # En lugar de eso, ya tenemos adaptadores de herramientas creados por mcp_server_tools
        # Solo devolvemos el mismo adaptador
        
        return mcp_tool
    except Exception as e:
        print(f"Error al registrar herramientas de Azure DevOps: {str(e)}")
        return None