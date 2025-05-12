# Guía de Implementación: Arquitectura MCP con AutoGen

## Introducción

Esta guía detalla cómo implementar una arquitectura basada en Model Context Protocol (MCP) con AutoGen, utilizando el proyecto MCP DevOps Agent como referencia. La arquitectura MCP ofrece un enfoque flexible y estructurado para crear aplicaciones que integran modelos de lenguaje con diversas herramientas y APIs, permitiendo a los agentes AI interactuar con sistemas externos de manera estandarizada.

## Conceptos Clave

### ¿Qué es MCP (Model Context Protocol)?

MCP es un protocolo de comunicación estandarizado que permite a los modelos de lenguaje interactuar con herramientas externas y APIs de manera consistente. Proporciona:

- Un formato común para solicitudes y respuestas
- Gestión de contexto estructurada
- Mecanismos de extensibilidad mediante herramientas (tools)
- Independencia del modelo subyacente

### ¿Qué es AutoGen?

AutoGen es un framework de Microsoft Research que facilita la creación de aplicaciones con múltiples agentes AI que pueden cooperar entre sí y utilizar herramientas externas. Características principales:

- Arquitectura multi-agente flexible
- Soporte para conversaciones complejas
- Integración con herramientas externas
- Capacidades de planificación y razonamiento

## Arquitectura de Referencia

El proyecto MCP DevOps Agent ilustra una implementación práctica de los conceptos MCP con AutoGen, organizándose en varias capas:

1. **Capa de Herramientas Base**: Implementa la funcionalidad core para interactuar con sistemas externos (ej. Azure DevOps)
2. **Capa de Servidor MCP**: Expone las herramientas como endpoints MCP estandarizados
3. **Capa de Cliente MCP**: Consume los servicios MCP y los hace disponibles para los agentes
4. **Capa de Agentes AutoGen**: Orquesta conversaciones utilizando herramientas MCP

```
┌─────────────────────┐
│  Agentes AutoGen    │
└───────────┬─────────┘
            │
┌───────────▼─────────┐
│   Cliente MCP       │
└───────────┬─────────┘
            │
┌───────────▼─────────┐
│   Servidor MCP      │
└───────────┬─────────┘
            │
┌───────────▼─────────┐
│ Herramientas Base   │
└─────────────────────┘
```

## Implementación Paso a Paso

### 1. Configuración del Entorno

Requisitos previos:

- Python 3.9 o superior
- Acceso a APIs externas según necesidad (ej. Azure DevOps PAT)
- Acceso a APIs de modelos de lenguaje (ej. OpenAI, Azure OpenAI)

Instalación de dependencias:

```bash
pip install pydantic requests python-dotenv autogen mcp-python
```

### 2. Implementación de Herramientas Base

Las herramientas base encapsulan la lógica de interacción con servicios externos. En el caso de MCP DevOps Agent, la clase `AzureDevOpsTool` implementa esta capa.

Pasos clave:

1. Crear una clase para cada servicio externo
2. Implementar métodos específicos para cada operación
3. Gestionar autenticación y configuración
4. Proporcionar funciones helper para procesamiento de datos

Ejemplo basado en `azdo_tools.py`:

```python
class MiIntegracionTool:
    """Clase para interactuar con Mi Servicio Externo"""

    def __init__(self):
        """Inicializar con credenciales desde variables de entorno"""
        self.api_key = os.environ.get("MI_SERVICIO_API_KEY")
        # Validación de configuración
        if not self.api_key:
            raise ValueError("Faltan credenciales en el archivo .env")

        # Configuración de cliente/headers
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def listar_recursos(self) -> List[Dict[str, Any]]:
        """Listar todos los recursos disponibles"""
        url = "https://mi-servicio.com/api/recursos"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('items', [])

    # Implementar otros métodos según necesidad...
```

### 3. Creación del Servidor MCP

El servidor MCP expone las herramientas como endpoints MCP estandarizados, definiendo schemas de entrada/salida y manejando la conversión entre llamadas MCP y las herramientas base.

Pasos clave:

1. Definir modelos Pydantic para parámetros de entrada
2. Crear un servidor MCP
3. Registrar herramientas con el servidor
4. Implementar handlers para cada herramienta

Ejemplo basado en `devops_server.py`:

```python
from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from mi_integracion_tools import MiIntegracionTool

# 1. Definir modelos para parámetros
class RecursosQuery(BaseModel):
    """Parámetros para listar recursos."""
    filtro: Annotated[Optional[str], Field(default=None, description="Filtro opcional para recursos")]

# 2. Crear función principal del servidor
async def serve() -> None:
    """Ejecutar el servidor MCP."""
    print("Iniciando el servidor MCP...")
    server = Server("mi-servicio-mcp")

    try:
        # Inicializar cliente
        cliente = MiIntegracionTool()
    except ValueError as e:
        print(f"Error al inicializar: {str(e)}")
        return

    # 3. Registrar herramientas
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="listar_recursos",
                description="Lista los recursos disponibles en el servicio externo.",
                inputSchema=RecursosQuery.model_json_schema(),
            ),
            # Más herramientas...
        ]

    # 4. Implementar handlers para cada herramienta
    @server.tool("listar_recursos")
    async def listar_recursos(params: RecursosQuery) -> Dict[str, Any]:
        try:
            recursos = cliente.listar_recursos()
            if params.filtro:
                # Aplicar filtro si existe
                recursos = [r for r in recursos if params.filtro.lower() in r.get('nombre', '').lower()]
            return {"recursos": recursos}
        except Exception as e:
            raise Exception(f"Error al listar recursos: {str(e)}")

    # Iniciar servidor
    await stdio_server.start(server)

if __name__ == "__main__":
    import asyncio
    asyncio.run(serve())
```

### 4. Creación del Cliente MCP

El cliente MCP consume los servicios expuestos por el servidor MCP y los hace disponibles para ser utilizados por agentes o aplicaciones.

```python
import autogen
from mcp.client import Client
from mcp.client.stdio import stdio_client

# Crear cliente MCP
cliente_mcp = stdio_client.create("mi-servicio-mcp")

# Configurar herramientas para AutoGen
config_list = [{"model": "gpt-4", "api_key": "tu-api-key"}]
llm_config = {
    "config_list": config_list,
    "tools": cliente_mcp.get_tool_specs(),
}

# Crear agente AutoGen con herramientas MCP
asistente = autogen.AssistantAgent(
    name="asistente",
    system_message="Eres un asistente útil con acceso a herramientas externas.",
    llm_config=llm_config,
)

usuario = autogen.UserProxyAgent(
    name="usuario",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
)

# Iniciar conversación
usuario.initiate_chat(
    asistente,
    message="Por favor, lista todos los recursos disponibles en el servicio.",
)
```

### 5. Orquestación con AutoGen

AutoGen permite crear sistemas multi-agente complejos que pueden utilizar las herramientas MCP en conversaciones.

Ejemplo de arquitectura multi-agente:

```python
# Definir agentes especializados
planner = autogen.AssistantAgent(
    name="planner",
    system_message="Eres un agente planificador que descompone tareas complejas.",
    llm_config={"config_list": config_list},
)

ejecutor = autogen.AssistantAgent(
    name="ejecutor",
    system_message="Ejecutas tareas utilizando herramientas externas.",
    llm_config=llm_config,  # Con herramientas MCP
)

usuario = autogen.UserProxyAgent(
    name="usuario",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
)

# Configurar grupo de chat
groupchat = autogen.GroupChat(
    agents=[usuario, planner, ejecutor],
    messages=[],
    max_round=10,
)

manager = autogen.GroupChatManager(groupchat=groupchat)

# Iniciar conversación
usuario.initiate_chat(
    manager,
    message="Analiza los recursos del servicio y crea un informe.",
)
```

## Patrones Avanzados

### Composición de Herramientas

Es posible combinar múltiples herramientas MCP para crear flujos de trabajo complejos:

```python
# Combinar clientes MCP de diferentes servicios
cliente_servicio1 = stdio_client.create("servicio1-mcp")
cliente_servicio2 = stdio_client.create("servicio2-mcp")

# Configurar herramientas combinadas
herramientas_combinadas = cliente_servicio1.get_tool_specs() + cliente_servicio2.get_tool_specs()

llm_config = {
    "config_list": config_list,
    "tools": herramientas_combinadas,
}
```

### Estado Compartido entre Agentes

Implementar mecanismos para compartir estado entre agentes:

```python
# Crear memoria compartida
memoria_compartida = {}

# Agentes con acceso a la memoria compartida
agente1 = autogen.AssistantAgent(
    name="agente1",
    system_message="Puedes almacenar información en la memoria compartida.",
    llm_config=llm_config,
)

# Función personalizada para gestionar memoria
def actualizar_memoria(key, value):
    memoria_compartida[key] = value
    return f"Información guardada: {key}={value}"

# Registrar función como herramienta
herramientas_adicionales = [
    {
        "type": "function",
        "function": {
            "name": "actualizar_memoria",
            "description": "Guarda información en memoria compartida",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["key", "value"],
            },
        },
    }
]

# Actualizar configuración con herramientas adicionales
llm_config_extendido = {
    "config_list": config_list,
    "tools": herramientas_combinadas + herramientas_adicionales,
}
```

## Mejores Prácticas

1. **Modularidad**: Separar claramente las capas de herramientas base, servidor MCP y cliente
2. **Gestión de Errores**: Implementar manejo robusto de errores en cada capa
3. **Autenticación**: Utilizar métodos seguros para gestionar credenciales (variables de entorno, Azure Key Vault)
4. **Validación**: Utilizar Pydantic para validar entradas y garantizar tipos correctos
5. **Documentación**: Proporcionar descripciones claras para herramientas y parámetros
6. **Pruebas**: Implementar tests unitarios y de integración para cada componente

## Adaptación a Otros Dominios

Esta arquitectura puede adaptarse a diversos dominios modificando las herramientas base y modelos. Ejemplos:

- **Analítica de Datos**: Herramientas para conectarse a fuentes de datos, realizar análisis y visualización
- **Gestión de Contenido**: Herramientas para interactuar con CMS, repositorios de documentos, etc.
- **Automatización IoT**: Herramientas para monitoreo y control de dispositivos IoT
- **Procesamiento Financiero**: Herramientas para interactuar con APIs financieras, análisis de riesgo, etc.

## Solución de Problemas

### Errores Comunes

1. **Fallo de Conexión**: Verificar configuración de red, credenciales y disponibilidad de servicios externos
2. **Formato Incorrecto**: Revisar schemas de entrada/salida y validación Pydantic
3. **Timeout**: Ajustar configuración de timeout para servicios lentos
4. **Permisos**: Verificar que las credenciales utilizadas tengan permisos suficientes

### Herramientas de Diagnóstico

- Habilitar logs detallados en servidor y cliente MCP
- Implementar puntos de traza en componentes críticos
- Utilizar herramientas de monitoreo para APIs externas

## Recursos Adicionales

- [Documentación oficial de MCP](https://github.com/microsoft/mcp)
- [Documentación de AutoGen](https://microsoft.github.io/autogen/)
- [Ejemplos de implementaciones MCP](https://github.com/microsoft/mcp-examples)
- [Mejores prácticas para APIs con Python](https://fastapi.tiangolo.com/tutorial/best-practices/)

---

Esta guía proporciona un punto de partida para implementar arquitecturas basadas en MCP con AutoGen. La flexibilidad de este enfoque permite adaptarlo a diversos casos de uso, aprovechando la potencia de los modelos de lenguaje mientras se mantiene una estructura modular y extensible.
