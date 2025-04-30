# MCP DevOps Agent

Un agente de DevOps basado en inteligencia artificial que utiliza el protocolo MCP (Model Context Protocol) para interactuar con Azure DevOps.

## Características

- Interacción con Azure DevOps a través de comandos en lenguaje natural
- Capacidad para gestionar repositorios, pipelines CI/CD y work items
- Filtrado de recursos por fecha utilizando expresiones en lenguaje natural
- Integración con Azure OpenAI para procesamiento de lenguaje natural

## Requisitos

- Python 3.11 o superior
- Una cuenta de Azure DevOps
- Acceso a Azure OpenAI o una API compatible

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

## Ejemplos de consultas

- "Muestra los work items de tipo bug de abril 2025"
- "Repositorios creados en marzo 2025"
- "Pipelines activos en 2025"
