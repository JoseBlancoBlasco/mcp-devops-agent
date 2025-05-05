from typing import Annotated, List, Dict, Any, Optional
import os
from pydantic import BaseModel, Field

from mcp.shared.exceptions import McpError
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ErrorData,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)

from azdo_tools import AzureDevOpsTool


class WorkItemsQuery(BaseModel):
    """Parámetros para consultar work items."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    work_item_type: Annotated[Optional[str], Field(default=None, description="Tipo de work item (Epic, User Story, Task, Bug, etc.)")] 
    date_filter: Annotated[Optional[str], Field(default=None, description="Filtro de fecha en lenguaje natural (ej. 'today', 'last week', 'last 30 days', '2023-01-01 to 2023-01-31')")] 
    state: Annotated[Optional[str], Field(default=None, description="Estado del work item (Active, Closed, etc.)")] 
    query_string: Annotated[Optional[str], Field(default=None, description="Consulta WIQL personalizada (si se proporciona, ignora otros filtros)")] 


class ProjectsQuery(BaseModel):
    """Parámetros para listar proyectos."""
    organization: Annotated[Optional[str], Field(default=None, description="Nombre o URL de la organización de Azure DevOps (opcional si está configurada en las variables de entorno)")] 


class RepositoriesQuery(BaseModel):
    """Parámetros para listar repositorios."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    date_filter: Annotated[Optional[str], Field(default=None, description="Filtro de fecha en lenguaje natural (ej. 'today', 'last week', 'last 30 days', '2023-01-01 to 2023-01-31')")] 


class PipelinesQuery(BaseModel):
    """Parámetros para listar pipelines."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    date_filter: Annotated[Optional[str], Field(default=None, description="Filtro de fecha en lenguaje natural (ej. 'today', 'last week', 'last 30 days', '2023-01-01 to 2023-01-31')")] 


class PullRequestsQuery(BaseModel):
    """Parámetros para listar pull requests."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    repository_id: Annotated[Optional[str], Field(default=None, description="ID del repositorio (opcional para listar PRs en todo el proyecto)")] 
    status: Annotated[Optional[str], Field(default="active", description="Estado del PR: active, abandoned, completed, all")] 


class WorkItemQuery(BaseModel):
    """Parámetros para obtener un work item específico."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    work_item_id: Annotated[int, Field(description="ID del work item a consultar")]


class RepositoryQuery(BaseModel):
    """Parámetros para obtener un repositorio específico."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    repository_id: Annotated[str, Field(description="ID del repositorio")]


class FileContentQuery(BaseModel):
    """Parámetros para obtener el contenido de un archivo."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    repository_id: Annotated[str, Field(description="ID del repositorio")]
    path: Annotated[str, Field(description="Ruta del archivo o directorio dentro del repositorio")]
    branch: Annotated[Optional[str], Field(default="main", description="Rama del repositorio (default: main)")]


class PullRequestCreateModel(BaseModel):
    """Parámetros para crear un pull request."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    repository_id: Annotated[str, Field(description="ID del repositorio")]
    source_branch: Annotated[str, Field(description="Nombre de la rama origen del cambio")]
    target_branch: Annotated[str, Field(description="Nombre de la rama destino del cambio")]
    title: Annotated[str, Field(description="Título del pull request")]
    description: Annotated[str, Field(description="Descripción detallada del pull request")]


class PullRequestCommentCreate(BaseModel):
    """Parámetros para añadir un comentario a un pull request."""
    project: Annotated[str, Field(description="Nombre del proyecto de Azure DevOps")]
    repository_id: Annotated[str, Field(description="ID del repositorio")]
    pull_request_id: Annotated[int, Field(description="ID del pull request")]
    comment: Annotated[str, Field(description="Texto del comentario a añadir")]
    thread_id: Annotated[Optional[int], Field(default=None, description="ID del hilo de comentarios (para responder a un comentario existente)")]

class GetMeQuery(BaseModel):
    """No necesita parámetros para obtener información del usuario autenticado"""
    pass


async def serve() -> None:
    """Ejecutar el servidor MCP para Azure DevOps."""
    print("Iniciando el servidor MCP para Azure DevOps...")
    server = Server("mcp-azuredevops")
    
    try:
        # Inicializar Azure DevOps client
        print("Inicializando cliente de Azure DevOps...")
        azdo = AzureDevOpsTool()
        print("Cliente de Azure DevOps inicializado correctamente.")
    except ValueError as e:
        print(f"Error al inicializar Azure DevOps client: {str(e)}")
        print("Asegúrate de tener configuradas las variables de entorno necesarias:")
        print("  - AZDO_PAT: Personal Access Token")
        print("  - AZDO_ORG: URL de la organización (https://dev.azure.com/miorganizacion)")
        return
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_projects",
                description="Lista los proyectos disponibles en una organización de Azure DevOps.",
                inputSchema=ProjectsQuery.model_json_schema(),
            ),
            Tool(
                name="list_work_items",
                description="Busca y lista work items en un proyecto de Azure DevOps con diversos filtros.",
                inputSchema=WorkItemsQuery.model_json_schema(),
            ),
            Tool(
                name="get_work_item",
                description="Obtiene todos los detalles de un work item específico por su ID.",
                inputSchema=WorkItemQuery.model_json_schema(),
            ),
            Tool(
                name="list_repositories",
                description="Lista los repositorios disponibles en un proyecto de Azure DevOps.",
                inputSchema=RepositoriesQuery.model_json_schema(),
            ),
            Tool(
                name="get_repository",
                description="Obtiene todos los detalles de un repositorio específico.",
                inputSchema=RepositoryQuery.model_json_schema(),
            ),
            Tool(
                name="get_file_content",
                description="Obtiene el contenido de un archivo o directorio de un repositorio.",
                inputSchema=FileContentQuery.model_json_schema(),
            ),
            Tool(
                name="list_pipelines",
                description="Lista los pipelines disponibles en un proyecto de Azure DevOps.",
                inputSchema=PipelinesQuery.model_json_schema(),
            ),
            Tool(
                name="list_pull_requests",
                description="Lista los pull requests en un proyecto o repositorio específico.",
                inputSchema=PullRequestsQuery.model_json_schema(),
            ),
            Tool(
                name="create_pull_request",
                description="Crea un nuevo pull request entre dos ramas.",
                inputSchema=PullRequestCreateModel.model_json_schema(),
            ),
            Tool(
                name="add_pull_request_comment",
                description="Añade un comentario a un pull request existente.",
                inputSchema=PullRequestCommentCreate.model_json_schema(),
            ),
            Tool(
                name="get_me",
                description="Obtiene información del usuario autenticado en Azure DevOps.",
                inputSchema=GetMeQuery.model_json_schema(),
            ),
        ]
    
    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="work_items",
                description="Busca work items en Azure DevOps",
                arguments=[
                    PromptArgument(
                        name="project", 
                        description="Nombre del proyecto", 
                        required=True
                    ),
                    PromptArgument(
                        name="work_item_type", 
                        description="Tipo de work item (Epic, User Story, Task, Bug, etc.)", 
                        required=False
                    ),
                    PromptArgument(
                        name="date_filter", 
                        description="Filtro de fecha en lenguaje natural", 
                        required=False
                    ),
                    PromptArgument(
                        name="state", 
                        description="Estado del work item", 
                        required=False
                    ),
                ],
            ),
            Prompt(
                name="pull_requests",
                description="Lista los pull requests en un proyecto o repositorio",
                arguments=[
                    PromptArgument(
                        name="project", 
                        description="Nombre del proyecto", 
                        required=True
                    ),
                    PromptArgument(
                        name="repository_id", 
                        description="ID del repositorio", 
                        required=False
                    ),
                    PromptArgument(
                        name="status", 
                        description="Estado del PR (active, abandoned, completed, all)", 
                        required=False
                    ),
                ],
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name, arguments: dict) -> list[TextContent]:
        try:
            if name == "list_projects":
                try:
                    args = ProjectsQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                projects = azdo.list_projects()
                
                if not projects:
                    return [TextContent(
                        type="text", 
                        text="No se encontraron proyectos en la organización."
                    )]
                
                # Formatea la salida para mostrar información relevante
                result = "Proyectos en Azure DevOps:\n\n"
                for idx, project in enumerate(projects, 1):
                    result += f"{idx}. {project.get('name')}\n"
                    result += f"   ID: {project.get('id')}\n"
                    result += f"   Descripción: {project.get('description') or 'N/A'}\n"
                    result += f"   Estado: {project.get('state')}\n"
                    result += f"   Último cambio: {project.get('lastUpdateTime')}\n"
                    result += f"   URL: {project.get('url')}\n\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "get_me":
                try:
                    args = GetMeQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                # Obtener información del usuario
                user_info = azdo.get_me()
                
                # Formatear la respuesta como texto
                if user_info:
                    result = f"Información del usuario autenticado:\n\n"
                    
                    # Añadir datos principales del usuario
                    result += f"📋 Detalles del usuario:\n"
                    result += f"- Nombre: {user_info.get('displayName', 'No disponible')}\n"
                    result += f"- Email: {user_info.get('mailAddress', 'No disponible')}\n"
                    result += f"- ID: {user_info.get('id', 'No disponible')}\n"
                    
                    # Añadir detalles adicionales si están disponibles
                    if 'descriptor' in user_info:
                        result += f"- Descriptor: {user_info.get('descriptor')}\n"
                        
                    # Añadir roles y permisos si están disponibles
                    if 'directoryAlias' in user_info:
                        result += f"- Alias: {user_info.get('directoryAlias')}\n"
                        
                    # URL de perfil
                    if 'url' in user_info:
                        result += f"\nURL del perfil: {user_info.get('url')}\n"
                else:
                    result = "No se pudo obtener información del usuario autenticado."
                    
                return [TextContent(type="text", text=result)]
            
            elif name == "list_work_items":
                try:
                    args = WorkItemsQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                project = args.project
                work_items = azdo.list_work_items(
                    query_string=args.query_string,
                    project=project,
                    work_item_type=args.work_item_type,
                    date_filter=args.date_filter,
                    state=args.state
                )
                
                if not work_items:
                    return [TextContent(
                        type="text", 
                        text=f"No se encontraron work items con los criterios especificados en el proyecto {project}."
                    )]
                
                # Formatea la salida para mostrar información relevante
                result = f"Work Items en {project}:\n\n"
                for idx, wi in enumerate(work_items, 1):
                    fields = wi.get('fields', {})
                    result += f"{idx}. #{wi.get('id')} - {fields.get('System.Title', 'Sin título')}\n"
                    result += f"   Tipo: {fields.get('System.WorkItemType', 'N/A')}\n"
                    result += f"   Estado: {fields.get('System.State', 'N/A')}\n"
                    result += f"   Asignado a: {fields.get('System.AssignedTo', {}).get('displayName', 'N/A')}\n"
                    result += f"   Creado: {fields.get('System.CreatedDate', 'N/A')}\n"
                    if 'System.Description' in fields and fields['System.Description']:
                        result += f"   Descripción: {fields['System.Description'][:150]}...\n"
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "get_work_item":
                try:
                    args = WorkItemQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                work_item = azdo.get_work_item(args.work_item_id, args.project)
                
                if not work_item:
                    return [TextContent(
                        type="text", 
                        text=f"No se encontró el work item {args.work_item_id} en el proyecto {args.project}."
                    )]
                
                # Formatea la salida para mostrar toda la información del work item
                fields = work_item.get('fields', {})
                result = f"Work Item #{work_item.get('id')} - {fields.get('System.Title', 'Sin título')}\n\n"
                result += f"Proyecto: {args.project}\n"
                result += f"Tipo: {fields.get('System.WorkItemType', 'N/A')}\n"
                result += f"Estado: {fields.get('System.State', 'N/A')}\n"
                result += f"Razón: {fields.get('System.Reason', 'N/A')}\n"
                result += f"Asignado a: {fields.get('System.AssignedTo', {}).get('displayName', 'N/A')}\n"
                result += f"Creado por: {fields.get('System.CreatedBy', {}).get('displayName', 'N/A')}\n"
                result += f"Creado: {fields.get('System.CreatedDate', 'N/A')}\n"
                result += f"Modificado: {fields.get('System.ChangedDate', 'N/A')}\n"
                
                # Descripción
                if 'System.Description' in fields and fields['System.Description']:
                    result += f"\nDescripción:\n{fields['System.Description']}\n\n"
                
                # Campos adicionales específicos del tipo de work item
                for field_name, field_value in fields.items():
                    if field_name.startswith('System.') or field_name.startswith('Microsoft.VSTS.Common.'):
                        continue  # Ya mostramos los campos básicos
                        
                    if isinstance(field_value, dict) and 'displayName' in field_value:
                        field_value = field_value['displayName']
                        
                    result += f"{field_name}: {field_value}\n"
                
                # Enlaces a otros work items
                if 'relations' in work_item:
                    result += "\nRelaciones:\n"
                    for relation in work_item['relations']:
                        rel_type = relation.get('rel', 'N/A')
                        rel_url = relation.get('url', 'N/A')
                        rel_id = rel_url.split('/')[-1] if '/' in rel_url else 'N/A'
                        
                        result += f"- {rel_type}: {rel_id}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "list_repositories":
                try:
                    args = RepositoriesQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                repositories = azdo.list_repositories(args.project, args.date_filter)
                
                if not repositories:
                    return [TextContent(
                        type="text", 
                        text=f"No se encontraron repositorios en el proyecto {args.project}."
                    )]
                
                # Formatea la salida para mostrar información relevante
                result = f"Repositorios en {args.project}:\n\n"
                for idx, repo in enumerate(repositories, 1):
                    result += f"{idx}. {repo.get('name')}\n"
                    result += f"   ID: {repo.get('id')}\n"
                    result += f"   Default branch: {repo.get('defaultBranch', 'N/A')}\n"
                    result += f"   Proyecto: {repo.get('project', {}).get('name', 'N/A')}\n"
                    result += f"   Size: {repo.get('size', 'N/A')}\n"
                    result += f"   URL: {repo.get('remoteUrl', 'N/A')}\n\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "get_repository":
                try:
                    args = RepositoryQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                repo_details = azdo.get_repository_details(args.repository_id, args.project)
                
                if not repo_details or 'repository' not in repo_details:
                    return [TextContent(
                        type="text", 
                        text=f"No se encontró el repositorio {args.repository_id} en el proyecto {args.project}."
                    )]
                
                repo = repo_details['repository']
                refs = repo_details.get('refs', [])
                stats = repo_details.get('stats', [])
                
                # Formatea la salida para mostrar toda la información del repositorio
                result = f"Repositorio: {repo.get('name')}\n\n"
                result += f"ID: {repo.get('id')}\n"
                result += f"Default branch: {repo.get('defaultBranch', 'N/A')}\n"
                result += f"Proyecto: {repo.get('project', {}).get('name', 'N/A')}\n"
                result += f"Size: {repo.get('size', 'N/A')}\n"
                result += f"URL: {repo.get('remoteUrl', 'N/A')}\n"
                result += f"WebURL: {repo.get('webUrl', 'N/A')}\n\n"
                
                # Referencias (ramas, tags)
                if refs:
                    result += "Referencias (branches, tags):\n"
                    for ref in refs[:10]:  # Limitamos a 10 refs para no sobrecargar la respuesta
                        name = ref.get('name', '').replace('refs/heads/', '')
                        result += f"- {name}\n"
                    
                    if len(refs) > 10:
                        result += f"... y {len(refs) - 10} más\n"
                    
                    result += "\n"
                
                # Estadísticas por branch
                if stats:
                    result += "Estadísticas por branch:\n"
                    for stat in stats[:5]:  # Limitamos a 5 branches para no sobrecargar
                        branch = stat.get('name', '').replace('refs/heads/', '')
                        commits = stat.get('count', 0)
                        result += f"- {branch}: {commits} commits\n"
                    
                    if len(stats) > 5:
                        result += f"... y {len(stats) - 5} más\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "get_file_content":
                try:
                    args = FileContentQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                content = azdo.get_file_content(
                    args.repository_id,
                    args.path,
                    args.branch,
                    args.project
                )
                
                if isinstance(content, dict) and 'value' in content:
                    # Es un directorio, formatear el listado de archivos
                    result = f"Contenido del directorio {args.path} (rama: {args.branch}):\n\n"
                    
                    for item in content.get('value', []):
                        item_type = 'DIR' if item.get('isFolder', False) else 'FILE'
                        item_path = item.get('path', 'N/A')
                        result += f"{item_type}: {item_path}\n"
                    
                    return [TextContent(type="text", text=result)]
                else:
                    # Es un archivo, mostrar su contenido
                    result = f"Contenido del archivo {args.path} (rama: {args.branch}):\n\n"
                    result += content
                    
                    return [TextContent(type="text", text=result)]
            
            elif name == "list_pipelines":
                try:
                    args = PipelinesQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                pipelines = azdo.list_pipelines(args.project, args.date_filter)
                
                if not pipelines:
                    return [TextContent(
                        type="text", 
                        text=f"No se encontraron pipelines en el proyecto {args.project}."
                    )]
                
                # Formatea la salida para mostrar información relevante
                result = f"Pipelines en {args.project}:\n\n"
                for idx, pipeline in enumerate(pipelines, 1):
                    result += f"{idx}. {pipeline.get('name')}\n"
                    result += f"   ID: {pipeline.get('id')}\n"
                    result += f"   Tipo: {pipeline.get('folder', 'N/A')}\n"
                    
                    # Si hay información del último run, mostrarla
                    if 'latestRun' in pipeline:
                        latest_run = pipeline['latestRun']
                        result += f"   Último run: #{latest_run.get('id', 'N/A')}\n"
                        result += f"   Estado: {latest_run.get('state', 'N/A')}\n"
                        result += f"   Resultado: {latest_run.get('result', 'N/A')}\n"
                        result += f"   Fecha: {latest_run.get('createdDate', 'N/A')}\n"
                    
                    result += "\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "list_pull_requests":
                try:
                    args = PullRequestsQuery(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                pull_requests = azdo.list_pull_requests(
                    args.repository_id,
                    args.status,
                    args.project
                )
                
                if not pull_requests:
                    repository_msg = f" en el repositorio {args.repository_id}" if args.repository_id else ""
                    return [TextContent(
                        type="text", 
                        text=f"No se encontraron pull requests{repository_msg} en el proyecto {args.project} con estado {args.status}."
                    )]
                
                # Formatea la salida para mostrar información relevante
                repository_msg = f" en el repositorio {args.repository_id}" if args.repository_id else ""
                result = f"Pull Requests {args.status}{repository_msg} en {args.project}:\n\n"
                
                for idx, pr in enumerate(pull_requests, 1):
                    result += f"{idx}. #{pr.get('pullRequestId')} - {pr.get('title')}\n"
                    result += f"   Estado: {pr.get('status')}\n"
                    result += f"   Creado por: {pr.get('createdBy', {}).get('displayName', 'N/A')}\n"
                    result += f"   Creado el: {pr.get('creationDate', 'N/A')}\n"
                    result += f"   Source branch: {pr.get('sourceRefName', '').replace('refs/heads/', '')}\n"
                    result += f"   Target branch: {pr.get('targetRefName', '').replace('refs/heads/', '')}\n"
                    result += f"   Repositorio: {pr.get('repository', {}).get('name', 'N/A')}\n"
                    result += f"   Descripción: {pr.get('description', 'N/A')[:150]}...\n\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "create_pull_request":
                try:
                    args = PullRequestCreateModel(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                pull_request = azdo.create_pull_request(
                    args.source_branch,
                    args.target_branch,
                    args.title,
                    args.description,
                    args.repository_id,
                    args.project
                )
                
                if not pull_request:
                    return [TextContent(
                        type="text", 
                        text=f"Error al crear el pull request en el repositorio {args.repository_id}."
                    )]
                
                # Formatea la salida para mostrar información del PR creado
                result = f"Pull Request creado correctamente:\n\n"
                result += f"ID: #{pull_request.get('pullRequestId')}\n"
                result += f"Título: {pull_request.get('title')}\n"
                result += f"Estado: {pull_request.get('status')}\n"
                result += f"Creado por: {pull_request.get('createdBy', {}).get('displayName', 'N/A')}\n"
                result += f"Source branch: {pull_request.get('sourceRefName', '').replace('refs/heads/', '')}\n"
                result += f"Target branch: {pull_request.get('targetRefName', '').replace('refs/heads/', '')}\n"
                result += f"URL: {pull_request.get('url', 'N/A')}\n"
                result += f"Web URL: {pull_request.get('_links', {}).get('web', {}).get('href', 'N/A')}\n"
                
                return [TextContent(type="text", text=result)]
            
            elif name == "add_pull_request_comment":
                try:
                    args = PullRequestCommentCreate(**arguments)
                except ValueError as e:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
                
                comment_result = azdo.add_pull_request_comment(
                    args.pull_request_id,
                    args.repository_id,
                    args.comment,
                    args.thread_id,
                    args.project
                )
                
                if not comment_result:
                    return [TextContent(
                        type="text", 
                        text=f"Error al añadir el comentario al pull request {args.pull_request_id}."
                    )]
                
                # Formatea la salida para confirmar que se añadió el comentario
                if 'id' in comment_result:
                    # Es una respuesta a un nuevo comentario
                    result = f"Comentario añadido correctamente al PR #{args.pull_request_id}:\n\n"
                    result += f"ID del comentario: {comment_result.get('id')}\n"
                    result += f"Contenido: {comment_result.get('content', 'N/A')}\n"
                else:
                    # Es una respuesta a un nuevo hilo
                    result = f"Nuevo hilo de comentarios añadido al PR #{args.pull_request_id}:\n\n"
                    result += f"ID del hilo: {comment_result.get('id')}\n"
                    comments = comment_result.get('comments', [])
                    if comments:
                        result += f"Comentario inicial: {comments[0].get('content', 'N/A')}\n"
                
                return [TextContent(type="text", text=result)]
            
            else:
                raise McpError(ErrorData(
                    code=INVALID_PARAMS, 
                    message=f"Herramienta no reconocida: {name}"
                ))
                
        except Exception as e:
            raise McpError(ErrorData(
                code=INTERNAL_ERROR, 
                message=f"Error al ejecutar la herramienta {name}: {str(e)}"
            ))
    
    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:
        if not arguments:
            raise McpError(ErrorData(code=INVALID_PARAMS, message="Se requieren argumentos para el prompt"))
        
        try:
            if name == "work_items":
                if "project" not in arguments:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message="El proyecto es requerido"))
                
                project = arguments["project"]
                work_item_type = arguments.get("work_item_type")
                date_filter = arguments.get("date_filter")
                state = arguments.get("state")
                
                work_items = azdo.list_work_items(
                    query_string=None,
                    project=project,
                    work_item_type=work_item_type,
                    date_filter=date_filter,
                    state=state
                )
                
                if not work_items:
                    return GetPromptResult(
                        description=f"No se encontraron work items en {project}",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(
                                    type="text", 
                                    text=f"No se encontraron work items con los criterios especificados en el proyecto {project}."
                                ),
                            )
                        ],
                    )
                
                # Formatea la salida para mostrar información relevante
                filters = []
                if work_item_type:
                    filters.append(f"tipo={work_item_type}")
                if date_filter:
                    filters.append(f"fecha={date_filter}")
                if state:
                    filters.append(f"estado={state}")
                
                filters_str = " ".join(filters)
                title = f"Work Items en {project}" + (f" ({filters_str})" if filters else "")
                
                result = f"{title}:\n\n"
                for idx, wi in enumerate(work_items, 1):
                    fields = wi.get('fields', {})
                    result += f"{idx}. #{wi.get('id')} - {fields.get('System.Title', 'Sin título')}\n"
                    result += f"   Tipo: {fields.get('System.WorkItemType', 'N/A')}\n"
                    result += f"   Estado: {fields.get('System.State', 'N/A')}\n"
                    result += f"   Asignado a: {fields.get('System.AssignedTo', {}).get('displayName', 'N/A')}\n"
                    result += f"   Creado: {fields.get('System.CreatedDate', 'N/A')}\n"
                    if 'System.Description' in fields and fields['System.Description']:
                        result += f"   Descripción: {fields['System.Description'][:150]}...\n"
                    result += "\n"
                
                return GetPromptResult(
                    description=title,
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=result),
                        )
                    ],
                )
            
            elif name == "pull_requests":
                if "project" not in arguments:
                    raise McpError(ErrorData(code=INVALID_PARAMS, message="El proyecto es requerido"))
                
                project = arguments["project"]
                repository_id = arguments.get("repository_id")
                status = arguments.get("status", "active")
                
                pull_requests = azdo.list_pull_requests(
                    repository_id,
                    status,
                    project
                )
                
                if not pull_requests:
                    repository_msg = f" en el repositorio {repository_id}" if repository_id else ""
                    return GetPromptResult(
                        description=f"No se encontraron pull requests {status}{repository_msg} en {project}",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(
                                    type="text", 
                                    text=f"No se encontraron pull requests{repository_msg} en el proyecto {project} con estado {status}."
                                ),
                            )
                        ],
                    )
                
                # Formatea la salida para mostrar información relevante
                repository_msg = f" en el repositorio {repository_id}" if repository_id else ""
                title = f"Pull Requests {status}{repository_msg} en {project}"
                
                result = f"{title}:\n\n"
                for idx, pr in enumerate(pull_requests, 1):
                    result += f"{idx}. #{pr.get('pullRequestId')} - {pr.get('title')}\n"
                    result += f"   Estado: {pr.get('status')}\n"
                    result += f"   Creado por: {pr.get('createdBy', {}).get('displayName', 'N/A')}\n"
                    result += f"   Creado el: {pr.get('creationDate', 'N/A')}\n"
                    result += f"   Source branch: {pr.get('sourceRefName', '').replace('refs/heads/', '')}\n"
                    result += f"   Target branch: {pr.get('targetRefName', '').replace('refs/heads/', '')}\n"
                    result += f"   Repositorio: {pr.get('repository', {}).get('name', 'N/A')}\n"
                    result += f"   Descripción: {pr.get('description', 'N/A')[:150]}...\n\n"
                
                return GetPromptResult(
                    description=title,
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=result),
                        )
                    ],
                )
            
            else:
                raise McpError(ErrorData(
                    code=INVALID_PARAMS, 
                    message=f"Prompt no reconocido: {name}"
                ))
                
        except Exception as e:
            return GetPromptResult(
                description=f"Error al ejecutar el prompt {name}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=str(e)),
                    )
                ],
            )
    
    print("Configurando opciones del servidor...")
    options = server.create_initialization_options()
    print("Iniciando servidor MCP (stdio)...")
    async with stdio_server() as (read_stream, write_stream):
        print("Servidor MCP listo y esperando conexiones...")
        await server.run(read_stream, write_stream, options, raise_exceptions=True)


if __name__ == "__main__":
    import asyncio
    
    # Ejecutar el servidor cuando se llama directamente al script
    asyncio.run(serve())