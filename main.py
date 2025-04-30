import os
import sys
import time
import subprocess
from dotenv import load_dotenv
import autogen
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import TextMessage
from mcp_server import DevOpsMCPServer
from mcp_client import DevOpsMCPClient
from azdo_tools import AzureDevOpsTool
import asyncio
import json
import datetime

# Cargar variables de entorno
load_dotenv()

def create_azure_model_client():
    """Crear un cliente para Azure OpenAI usando variables de entorno"""
    try:
        az_model_client = AzureOpenAIChatCompletionClient(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        print("Cliente AzureOpenAIChatCompletionClient creado correctamente")
        return az_model_client
    except Exception as e:
        print(f"Error al crear AzureOpenAIChatCompletionClient: {str(e)}")
        print("Intentando configuración alternativa...")
        
        # Configuración alternativa si la anterior falla
        config_list = [{
            "model": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_type": "azure",
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        }]
        
        return config_list

def create_devops_agent(model_client):
    """Crear un agente DevOps con capacidades MCP"""
    # Según la documentación oficial, AssistantAgent acepta model_client
    devops_agent = AssistantAgent(
        name="devops_expert",
        system_message="""Eres un experto en DevOps especializado en Azure DevOps.
Puedes ayudar con gestión de repositorios, pipelines CI/CD, work items y otras tareas de DevOps.
Tienes acceso a herramientas MCP (Model Context Protocol) que te permiten interactuar con servicios externos.
Puedes listar repositorios, pipelines y work items en Azure DevOps.
También puedes crear nuevos work items, verificar el estado de builds y gestionar pull requests.

NUEVA CAPACIDAD: Ahora puedes filtrar recursos por fecha utilizando expresiones en lenguaje natural como:
- "Muestra los work items de tipo bug de abril 2025"
- "Repositorios creados en marzo 2025"
- "Pipelines activos en 2025"

Cuando el usuario te pida información específica sobre Azure DevOps como repositorios, work items o pipelines,
DEBES usar las herramientas correspondientes para obtener datos reales en lugar de inventar respuestas.

Organización de Azure DevOps: {}
Proyecto por defecto: {}
Fecha actual: {}

Responde en español a menos que se te solicite otro idioma.""".format(
            os.getenv("AZDO_ORG", "No configurado"), 
            os.getenv("AZDO_PROJECT", "No configurado"),
            datetime.datetime.now().strftime("%d de %B de %Y")
        ),
        model_client=model_client
    )
    
    return devops_agent

def create_user_proxy():
    """Crear un agente proxy de usuario para interactuar con el agente DevOps"""
    # Usar solo el nombre para evitar errores de parámetros no compatibles
    user_proxy = UserProxyAgent(
        name="dev_user",
    )
    
    return user_proxy

# Función para ejecutar comandos de Azure DevOps a través de los tools
async def execute_azdo_command(mcp_client, command, args=None):
    """Ejecuta un comando de Azure DevOps y devuelve el resultado formateado"""
    try:
        result = None
        
        if command == "list_repositories":
            project = args.get("project") if args else None
            date_filter = args.get("date_filter") if args else None
            repos = mcp_client.list_repositories(project, date_filter)
            result = [{"name": repo.get("name"), "id": repo.get("id")} for repo in repos]
            
        elif command == "list_work_items":
            project = args.get("project") if args else None
            query = args.get("query") if args else None
            work_item_type = args.get("work_item_type") if args else None
            date_filter = args.get("date_filter") if args else None
            state = args.get("state") if args else None
            
            work_items = mcp_client.list_work_items(query, project, work_item_type, date_filter, state)
            result = []
            for wi in work_items:
                result.append({
                    "id": wi.get("id"),
                    "title": wi.get("fields", {}).get("System.Title", "Sin título"),
                    "state": wi.get("fields", {}).get("System.State", "Desconocido"),
                    "type": wi.get("fields", {}).get("System.WorkItemType", "Desconocido")
                })
                
        elif command == "list_pipelines":
            project = args.get("project") if args else None
            date_filter = args.get("date_filter") if args else None
            pipelines = mcp_client.list_pipelines(project, date_filter)
            result = [{"name": pipeline.get("name"), "id": pipeline.get("id")} for pipeline in pipelines]
        
        elif command == "parse_natural_query":
            query_text = args.get("query_text") if args else ""
            if query_text:
                result = mcp_client.parse_natural_query(query_text)
            else:
                result = {"error": "Consulta vacía"}
                
        return result
    except Exception as e:
        return {"error": str(e)}

# Nueva función para manejar la conversación interactiva
async def interactive_chat(devops_agent, mcp_client):
    """Función para gestionar una conversación interactiva con el agente DevOps"""
    print("\n== CHAT INTERACTIVO CON EL AGENTE DEVOPS ==")
    print("Escribe tus preguntas y el agente te responderá.")
    print("Escribe 'exit', 'salir' o 'terminar' para finalizar la conversación.")
    print("Escribe 'debug' para activar/desactivar el modo de depuración.")
    print("\nConexión a Azure DevOps:")
    print(f"Organización: {os.getenv('AZDO_ORG', 'No configurado')}")
    print(f"Proyecto por defecto: {os.getenv('AZDO_PROJECT', 'No configurado')}\n")
    print("NUEVAS CAPACIDADES:")
    print("- Filtrado por fecha en lenguaje natural")
    print("- Búsqueda de recursos por criterios temporales")
    print("- Consultas en lenguaje natural\n")
    
    conversation_history = []
    debug_mode = False
    
    while True:
        # Solicitar entrada al usuario
        user_input = input("\n🧑 TÚ: ")
        
        # Verificar si el usuario quiere salir
        if user_input.lower() in ["exit", "salir", "terminar"]:
            print("\nFinalizando conversación...")
            break
            
        # Activar/desactivar modo debug
        if user_input.lower() == "debug":
            debug_mode = not debug_mode
            print(f"\nModo debug {'activado' if debug_mode else 'desactivado'}")
            continue
            
        # Procesar comandos especiales
        if user_input.startswith("!"):
            parts = user_input[1:].split(" ", 1)
            command = parts[0].lower()
            args = json.loads(parts[1]) if len(parts) > 1 else None
            
            if command in ["repos", "repositories"]:
                result = await execute_azdo_command(mcp_client, "list_repositories", args)
                print(f"\n📋 Repositorios: {json.dumps(result, indent=2, ensure_ascii=False)}")
                continue
                
            elif command in ["items", "workitems"]:
                result = await execute_azdo_command(mcp_client, "list_work_items", args)
                print(f"\n📋 Work Items: {json.dumps(result, indent=2, ensure_ascii=False)}")
                continue
                
            elif command in ["pipes", "pipelines"]:
                result = await execute_azdo_command(mcp_client, "list_pipelines", args)
                print(f"\n📋 Pipelines: {json.dumps(result, indent=2, ensure_ascii=False)}")
                continue
                
            elif command in ["consulta", "query"]:
                result = await execute_azdo_command(mcp_client, "parse_natural_query", {"query_text": parts[1] if len(parts) > 1 else ""})
                print(f"\n📋 Resultado de la consulta: {json.dumps(result, indent=2, ensure_ascii=False)}")
                continue
        
        # Verificar si es una consulta en lenguaje natural sobre fechas
        date_indicators = ["2025", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", 
                         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        
        resource_indicators = ["repositorios", "repos", "work items", "tareas", "bugs", 
                             "historias", "pipelines", "builds"]
                             
        if any(indicator in user_input.lower() for indicator in date_indicators) and \
           any(indicator in user_input.lower() for indicator in resource_indicators):
            
            if debug_mode:
                print("\n[DEBUG] Detectada consulta en lenguaje natural con filtro de fecha")
            
            # Intentar procesar como consulta natural antes de pasar al LLM
            try:
                result = mcp_client.parse_natural_query(user_input)
                # Si tenemos resultados significativos, mostrarlos
                if result and not isinstance(result, dict) and not result.get("error"):
                    print(f"\n📋 Resultado de la consulta natural: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    # Agregar una nota sobre el procesamiento
                    print("\n🤖 AGENTE DEVOPS: He procesado tu consulta de filtrado por fecha directamente.")
                    print("Estos son los resultados que coinciden con tus criterios.")
                    continue
            except Exception as e:
                if debug_mode:
                    print(f"\n[DEBUG] Error al procesar consulta natural: {str(e)}")
        
        # Crear mensaje del usuario
        user_message = TextMessage(content=user_input, source="dev_user")
        conversation_history.append(user_message)
        
        try:
            # Enviar mensaje al agente DevOps
            result = await devops_agent.run(task=user_message)
            
            # Extraer y mostrar la respuesta
            if hasattr(result, "messages") and len(result.messages) > 0:
                assistant_message = result.messages[-1]
                conversation_history.append(assistant_message)
                
                print(f"\n🤖 AGENTE DEVOPS: {assistant_message.content}")
                
                # Mostrar detalles extra en modo debug
                if debug_mode:
                    print("\n[DEBUG] Respuesta completa:")
                    print(f"Type: {type(result).__name__}")
                    print(f"Stop reason: {result.stop_reason}")
                    if hasattr(result, "messages"):
                        print(f"Mensajes: {len(result.messages)}")
            else:
                print("\n🤖 AGENTE DEVOPS: Lo siento, no pude generar una respuesta.")
        
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            if debug_mode:
                import traceback
                traceback.print_exc()

def main():
    mcp_server = None
    try:
        # Verificar y mostrar variables de entorno (sin revelar valores sensibles)
        env_vars = {
            "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION"),
            "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "AZDO_ORG": os.getenv("AZDO_ORG"),
            "AZDO_PROJECT": os.getenv("AZDO_PROJECT"),
        }
        
        print("Variables de entorno configuradas:")
        for key, value in env_vars.items():
            if key in ["AZURE_OPENAI_API_KEY", "AZDO_PAT"]:
                continue  # No mostrar claves o tokens
            status = "✅" if value else "❌"
            print(f"{status} {key}: {value if value else 'No configurado'}")
        
        # Comprobar PAT sin mostrar el valor
        azdo_pat = os.getenv("AZDO_PAT")
        print(f"{'✅' if azdo_pat else '❌'} AZDO_PAT: {'Configurado' if azdo_pat else 'No configurado'}")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        print(f"{'✅' if azure_api_key else '❌'} AZURE_OPENAI_API_KEY: {'Configurado' if azure_api_key else 'No configurado'}")
        
        # Verificar instalación correcta de MCP
        try:
            import mcp
            print(f"Biblioteca MCP instalada: versión {mcp.__version__}")
        except (ImportError, AttributeError):
            print("¡Advertencia! No se pudo verificar la instalación de MCP.")
        
        # Iniciar servidor MCP - usando el módulo MCP directamente
        print("Iniciando entorno MCP para DevOps...")
        command = "python -m mcp.server"
        
        # Crear servidor MCP
        mcp_server = DevOpsMCPServer(command=command)
        mcp_server.start()
        
        # Pausa para asegurar que el servidor está listo
        time.sleep(2)
        
        # Crear cliente MCP con el mismo comando
        mcp_client = DevOpsMCPClient(command=command)
        mcp_client.initialize()
        
        # Crear el cliente del modelo para Azure OpenAI
        az_model_client = create_azure_model_client()
        
        # Crear agente DevOps
        devops_agent = create_devops_agent(az_model_client)
        
        # Registrar herramientas MCP con el agente
        mcp_client.register_to_agent(devops_agent)
        mcp_client.register_custom_tools()
        
        # Iniciar conversación interactiva
        print("\n" + "="*50)
        print("Agente DevOps MCP iniciado.")
        print("="*50 + "\n")
        
        # Iniciar chat interactivo
        asyncio.run(interactive_chat(devops_agent, mcp_client))
    
    except Exception as e:
        print(f"Error al ejecutar el agente: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Asegurar que el servidor se cierre al terminar
        if mcp_server is not None:
            print("\nDeteniendo servidor MCP...")
            mcp_server.stop()
            print("Servidor MCP detenido.")

if __name__ == "__main__":
    main()