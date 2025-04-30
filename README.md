# MCP DevOps Agent

Un agente de DevOps basado en inteligencia artificial que utiliza el protocolo MCP (Model Context Protocol) para interactuar con Azure DevOps.

## Características

- Interacción con Azure DevOps a través de comandos en lenguaje natural
- Capacidad para gestionar repositorios, pipelines CI/CD y work items
- Filtrado de recursos por fecha utilizando expresiones en lenguaje natural
- Integración con Azure OpenAI para procesamiento de lenguaje natural
- Framework AutoGen para conversaciones interactivas con IA avanzada
- Detección automática de consultas sobre work items por ID

## Tecnologías utilizadas

- **MCP (Model Context Protocol)**: Protocolo para la comunicación entre modelos de IA y herramientas externas
- **AutoGen**: Framework de agentes conversacionales que permite crear diálogos complejos con asistentes de IA
- **Azure DevOps API**: Interfaz para interactuar con repositorios, work items, pipelines y otros recursos
- **Azure OpenAI**: Servicios de procesamiento de lenguaje natural para entender consultas en lenguaje natural

## Requisitos

- Python 3.11 o superior
- Una cuenta de Azure DevOps
- Acceso a Azure OpenAI o una API compatible
- Paquetes Python: autogen-agentchat, autogen-ext[openai,azure,mcp]

## Configuración

1. Clone este repositorio
2. Instale las dependencias: `pip install -r requirements.txt`
3. Configure las variables de entorno (ver sección siguiente)

## Variables de entorno

El proyecto requiere las siguientes variables de entorno:

```
AZURE_OPENAI_DEPLOYMENT_NAME=nombre_del_modelo
AZURE_OPENAI_API_VERSION=version_de_api
AZURE_OPENAI_ENDPOINT=url_del_endpoint
AZURE_OPENAI_API_KEY=su_api_key
AZDO_ORG=nombre_de_organizacion
AZDO_PROJECT=nombre_del_proyecto
AZDO_PAT=personal_access_token
```

## Uso

Ejecute el script principal:

```
python main.py
```

## Comandos especiales

- `!repos` - Listar repositorios
- `!items` - Listar work items
- `!pipes` - Listar pipelines
- `!consulta "texto"` - Realizar una consulta en lenguaje natural
- `!item <id>` - Consultar un work item específico por su ID
- `debug` - Activar/desactivar modo de depuración

## Ejemplos de consultas

- "Muestra los work items de tipo bug de abril 2025"
- "Repositorios creados en marzo 2025"
- "Pipelines activos en 2025"
- "Dame información sobre el item 21101"
- "Muéstrame los detalles del work item 5432"

## Arquitectura

El proyecto está estructurado en varios componentes principales:

- `main.py`: Punto de entrada que configura el entorno, inicializa el servidor MCP y crea los agentes de AutoGen
- `mcp_server.py`: Gestiona el servidor MCP que permite la comunicación entre el agente y las herramientas externas
- `mcp_client.py`: Cliente para conectar los agentes de AutoGen con el servidor MCP
- `azdo_tools.py`: Implementación de las herramientas para interactuar con Azure DevOps

## Colaboración

Las contribuciones son bienvenidas. Para colaborar:

1. Fork el repositorio
2. Cree una rama con la funcionalidad: `git checkout -b feature/nueva-funcionalidad`
3. Commit sus cambios: `git commit -am 'Añadir nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Envíe un Pull Request
