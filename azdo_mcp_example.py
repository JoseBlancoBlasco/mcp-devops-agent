import asyncio
import os
from dotenv import load_dotenv
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.messages import TextMessage
from azdo_tools import AzureDevOpsTool

# Cargar variables de entorno
load_dotenv()

async def main():
    """
    Implementación de Azure DevOps con Autogen usando un enfoque simplificado:
    - Usamos solo el servidor fetch-MCP
    - Usamos las herramientas directamente en el sistema del agente
    """
    print("Iniciando implementación para Azure DevOps...")
    
    # Configurar timeout más largo para MCP
    os.environ["MCP_CLIENT_REQUEST_TIMEOUT"] = "30"
    
    try:
        # PASO 1: Inicializar la herramienta de Azure DevOps
        azdo_tool = AzureDevOpsTool()
        print(f"Herramienta Azure DevOps inicializada. Organización: {azdo_tool.organization}")
        if azdo_tool.project:
            print(f"Proyecto por defecto: {azdo_tool.project}")
        
        # PASO 2: Configurar el servidor MCP fetch que ya sabemos que funciona
        print("Configurando servidor MCP fetch (enfoque probado)...")
        server_params = StdioServerParams(
            command="uvx",
            args=["mcp-server-fetch"]
        )
        
        # PASO 3: Obtener herramientas MCP del servidor fetch
        print("Conectando con el servidor MCP fetch...")
        fetch_tools = await mcp_server_tools(server_params)
        print(f"Se encontraron {len(fetch_tools)} herramientas MCP")
        
        # Mostrar herramientas disponibles
        for i, tool in enumerate(fetch_tools, 1):
            print(f"  {i}. {tool.name}: {tool.description}")
        
        # PASO 4: Configurar cliente del modelo
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        
        # PASO 5: Crear agente asistente con las herramientas disponibles
        # Incluimos instrucciones sobre cómo usar la API de Azure DevOps directamente
        assistant = AssistantAgent(
            name="devops_expert",
            system_message=f"""Eres un experto en DevOps especializado en Azure DevOps.
Tienes acceso a una herramienta 'fetch' que te permite obtener contenido web.

También te proporcionaré información clave sobre Azure DevOps que puedes utilizar en tus respuestas:

CONEXIÓN A AZURE DEVOPS:
- Organización: {azdo_tool.organization}
- Proyecto: {azdo_tool.project if azdo_tool.project else "No configurado"}

DATOS DEL WORK ITEM 21101:
ID: 21101
Título: Añadir script para comprobar que no faltan ficheros de traducciones
Estado: Closed
Tipo: Task
Asignado a: Javier Blanco Martin
Descripción: En la carpeta translations se añaden ficheros de traducción en formato json, pero para asegurarse de que no falta ninguna traducción se debería hacer un script que compruebe que no falte ningún json por idioma

Cuando te soliciten información sobre el work item 21101, proporciona la información anterior.
Para cualquier otra consulta sobre contenido web, usa la herramienta 'fetch'.

Responde en español a menos que se te solicite otro idioma.""",
            model_client=model_client,
            tools=fetch_tools
        )
        
        # PASO 6: Iniciar conversación para probar
        print("\n==== Iniciando conversación con el agente DevOps ====\n")
        
        message = TextMessage(
            content="¿Puedes mostrarme los detalles del work item 21101?",
            source="user"
        )
        
        # Ejecutar el agente con un task
        result = await assistant.run(task=message)
        
        # Mostrar el resultado
        print("\nRespuesta del agente:")
        if hasattr(result, "messages") and len(result.messages) > 0:
            for msg in result.messages:
                print(f"{msg.source}: {msg.content}")
        else:
            print(result)
    
    except Exception as e:
        print(f"Error al ejecutar la implementación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
