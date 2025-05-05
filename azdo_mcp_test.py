import asyncio
import os
import sys
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
    - Usamos nuestro servidor MCP de Azure DevOps
    - Permitimos al agente usar las herramientas de Azure DevOps directamente
    - Modo interactivo para mantener una conversación con el agente
    """
    print("Iniciando implementación para Azure DevOps...")
    
    # Configurar timeout más largo para MCP
    os.environ["MCP_CLIENT_REQUEST_TIMEOUT"] = "60"
    
    try:
        # PASO 1: Inicializar la herramienta de Azure DevOps
        azdo_tool = AzureDevOpsTool()
        print(f"Herramienta Azure DevOps inicializada. Organización: {azdo_tool.organization}")
        if azdo_tool.project:
            print(f"Proyecto por defecto: {azdo_tool.project}")
        
        # PASO 2: Configurar nuestro servidor MCP de Azure DevOps
        print("Configurando servidor MCP de Azure DevOps...")
        # Obtener la ruta del script actual y del servidor
        current_dir = os.path.dirname(os.path.abspath(__file__))
        server_script = os.path.join(current_dir, "devops_server.py")
        
        server_params = StdioServerParams(
            command=sys.executable,  # Usar el intérprete Python actual
            args=[server_script]
        )
        
        # PASO 3: Obtener herramientas MCP del servidor de Azure DevOps
        print("Conectando con el servidor MCP de Azure DevOps...")
        azdo_tools = await mcp_server_tools(server_params)
        print(f"Se encontraron {len(azdo_tools)} herramientas MCP")
        
        # Mostrar herramientas disponibles
        for i, tool in enumerate(azdo_tools, 1):
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
        assistant = AssistantAgent(
            name="devops_expert",
            system_message=f"""Eres un experto en DevOps especializado en Azure DevOps.
Tienes acceso a varias herramientas MCP que te permiten interactuar con Azure DevOps.

CONEXIÓN A AZURE DEVOPS:
- Organización: {os.getenv("AZDO_ORG")}
- Proyecto por defecto: {os.getenv("AZDO_PROJECT") if os.getenv("AZDO_PROJECT") else "No configurado"}

Puedes usar estas herramientas para:
- Listar proyectos en la organización
- Obtener información sobre work items
- Listar repositorios Git
- Ver pull requests
- Consultar pipelines
- Y mucho más

Cuando te soliciten información sobre Azure DevOps, SIEMPRE usa las herramientas MCP disponibles
para obtener datos en tiempo real, en lugar de proporcionar información estática.

Responde de manera concisa y en español a menos que se te solicite otro idioma.""",
            model_client=model_client,
            tools=azdo_tools
        )
        
        # PASO 6: Crear un agente humano para mantener la conversación
        user_proxy = UserProxyAgent(
            name="human"
        )

        # PASO 7: Iniciar modo de conversación interactiva
        print("\n==== Conversación interactiva con el experto en Azure DevOps ====")
        print("(Escribe 'salir', 'exit' o 'q' para terminar la conversación)")
        print("-" * 70)
        
        conversation_active = True
        while conversation_active:
            # Solicitar entrada del usuario
            user_input = input("\n📝 Tú: ")
            
            # Verificar si el usuario quiere salir
            if user_input.lower() in ["salir", "exit", "q", "quit"]:
                print("Finalizando conversación...")
                conversation_active = False
                continue
            
            if not user_input.strip():
                print("Por favor, ingresa un mensaje válido.")
                continue
            
            # Crear un mensaje de texto para enviar al agente
            message = TextMessage(
                content=user_input,
                source="human"
            )
            
            print("\n⏳ Procesando...")
            
            # Ejecutar el agente con el mensaje
            result = await assistant.run(task=message)
            
            # Mostrar la respuesta
            print("\n🤖 Asistente:", end=" ")
            
            if hasattr(result, "messages") and len(result.messages) > 0:
                for msg in result.messages:
                    if msg.source == "devops_expert":
                        # Si el contenido es una llamada a función o resultado de función, formatear
                        if str(msg.content).startswith("[FunctionCall(") or str(msg.content).startswith("[FunctionExecutionResult("):
                            if "FunctionCall" in str(msg.content):
                                print("\n   🔧 Consultando Azure DevOps...", end="")
                            continue
                        # Imprimir contenido normal
                        print(msg.content)
            else:
                print(result)
        
        print("\n==== Conversación finalizada ====")
    
    except Exception as e:
        print(f"\n❌ Error al ejecutar la implementación: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nConversación interrumpida por el usuario. ¡Hasta pronto!")
