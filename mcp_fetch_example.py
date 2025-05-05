import asyncio
import os
from dotenv import load_dotenv
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.messages import TextMessage

# Cargar variables de entorno
load_dotenv()

async def main():
    """
    Implementación minimalista de MCP con Autogen usando mcp-server-fetch.
    Usando el enfoque más compatible y simple posible.
    """
    print("Iniciando implementación MCP con servidor fetch...")
    
    # Configurar timeout más largo
    os.environ["MCP_CLIENT_REQUEST_TIMEOUT"] = "30"
    
    # Configurar servidor MCP para fetch web usando uvx
    print("Configurando servidor MCP fetch...")
    server_params = StdioServerParams(
        command="uvx",
        args=["mcp-server-fetch"]
    )
    
    # Obtener herramientas MCP
    print("Conectando con el servidor MCP fetch...")
    try:
        tools = await mcp_server_tools(server_params)
        print(f"¡Éxito! Se encontraron {len(tools)} herramientas MCP")
        
        # Mostrar herramientas disponibles
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name}: {tool.description}")
        
        # Configurar cliente del modelo
        model_client = AzureOpenAIChatCompletionClient(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY")
        )
        
        # Crear agente asistente
        assistant = AssistantAgent(
            name="fetch_agent",
            system_message="""Eres un asistente que puede buscar y recuperar contenido web.
Tienes acceso a una herramienta de MCP llamada 'fetch' que te permite obtener contenido de URLs.
IMPORTANTE: Cuando te pidan información de alguna página web, DEBES usar la herramienta 'fetch'.
Responde de manera concisa y en español.""",
            model_client=model_client,
            tools=tools
        )
        
        # Manera más simple de usar el agente directamente
        print("\n==== Iniciando conversación con el agente ====\n")
        
        # Crear un mensaje de texto para enviar al agente
        message = TextMessage(
            content="¿Puedes obtener información del blog de Victor Dibia en https://newsletter.victordibia.com/p/how-to-use-mcp-anthropic-mcp-tools y resumir lo que dice sobre MCP?",
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
        print(f"Error al iniciar MCP: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Sugerencias para solucionar problemas comunes
        print("\nSugerencias para solucionar problemas:")
        print("1. Verifica que tengas instalado 'mcp-server-fetch' con: pip install -U autogen-ext[mcp] json-schema-to-pydantic>=0.2.2")
        print("2. Instala el servidor fetch con: uv tool install mcp-server-fetch")
        print("3. Actualiza la shell con: uv tool update-shell")
        print("4. Si usas WSL, asegúrate de que la ruta de instalación de herramientas esté en tu PATH")

if __name__ == "__main__":
    asyncio.run(main())
