# MCP DevOps Agent

Un agente de DevOps basado en inteligencia artificial que utiliza el protocolo MCP (Model Context Protocol) para interactuar con Azure DevOps.

## Características

- Interacción con Azure DevOps a través de comandos en lenguaje natural
- Capacidad para gestionar repositorios, pipelines CI/CD y work items
- Gestión completa de work items (creación, actualización, comentarios, clonación, vinculación)
- Operaciones con pull requests (creación, listado, comentarios)
- Filtrado de recursos por fecha utilizando expresiones en lenguaje natural
- Integración con Azure OpenAI para procesamiento de lenguaje natural
- Framework AutoGen para conversaciones interactivas con IA avanzada
- Detección automática de consultas sobre work items por ID
- Visualización mejorada de respuestas JSON con formato legible y estructurado

## Tecnologías utilizadas

- **MCP (Model Context Protocol)**: Protocolo para la comunicación entre modelos de IA y herramientas externas
- **AutoGen**: Framework de agentes conversacionales que permite crear diálogos complejos con asistentes de IA
- **Azure DevOps API**: Interfaz para interactuar con repositorios, work items, pipelines y otros recursos
- **Azure OpenAI**: Servicios de procesamiento de lenguaje natural para entender consultas en lenguaje natural

## Funcionalidades principales

### Gestión de Work Items

- Creación, actualización y consulta de work items
- Adición de comentarios a work items existentes
- Clonación de work items
- Vinculación entre work items
- Gestión de etiquetas
- Consulta de historial de cambios

### Gestión de Repositorios

- Listado de repositorios
- Obtención de detalles de repositorios
- Acceso al contenido de archivos
- Navegación por directorios

### Operaciones con Pull Requests

- Creación de pull requests entre ramas
- Listado de pull requests con filtros
- Adición de comentarios a pull requests

### Gestión de Pipelines

- Listado de pipelines
- Visualización de estado y resultados

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
- `!prs` - Listar pull requests
- `!consulta "texto"` - Realizar una consulta en lenguaje natural
- `!item <id>` - Consultar un work item específico por su ID
- `!create_item "título" "tipo"` - Crear un nuevo work item
- `!update_item <id> "campo" "valor"` - Actualizar un campo en un work item
- `!clone_item <id> "nuevo_título"` - Clonar un work item existente
- `!get_me` - Obtener información del usuario autenticado con formato mejorado
- `debug` - Activar/desactivar modo de depuración

## Ejemplos de consultas

- "Muestra los work items de tipo bug de abril 2025"
- "Crea un nuevo work item de tipo Bug con título 'Error en login'"
- "Actualiza el estado del work item 5432 a 'Closed'"
- "Añade un comentario al work item 1234 diciendo 'Revisado y aprobado'"
- "Crea un pull request desde la rama 'feature/login' hacia 'main'"
- "Repositorios creados en marzo 2025"
- "Pipelines activos en 2025"
- "Dame información sobre el item 21101"
- "Muéstrame los detalles del work item 5432"
- "Ejecuta get_me para ver mi información de usuario"

## Arquitectura

El proyecto está estructurado en varios componentes principales:

- `main.py`: Punto de entrada que configura el entorno, inicializa el servidor MCP y crea los agentes de AutoGen
- `devops_server.py`: Gestiona el servidor MCP que permite la comunicación entre el agente y las herramientas externas
- `devops_tools.py`: Implementación de las herramientas para interactuar con Azure DevOps, incluyendo:
  - Gestión de work items (creación, actualización, comentarios, clonación)
  - Operaciones con repositorios y código fuente
  - Manejo de pull requests
  - Gestión de pipelines CI/CD

## Mejoras recientes

- **Gestión completa de work items**: Se ha implementado funcionalidad para crear, actualizar, comentar, clonar y vincular work items.
- **Operaciones con pull requests**: Ahora es posible crear, listar y comentar pull requests.
- **Herramientas de etiquetado**: Se han añadido funciones para gestionar etiquetas en work items.
- **Historial de work items**: Posibilidad de consultar el historial de cambios de un work item.
- **Visualización de respuestas JSON**: Se ha mejorado la interpretación y visualización de respuestas JSON para facilitar la lectura de datos estructurados.
- **Detección inteligente de formato**: El sistema ahora detecta automáticamente si una respuesta es JSON y aplica un formato adecuado.
- **Indentación y estructuración**: Las respuestas JSON ahora se muestran con indentación para mejorar su legibilidad.

## Colaboración

Las contribuciones son bienvenidas. Para colaborar:

1. Fork el repositorio
2. Cree una rama con la funcionalidad: `git checkout -b feature/nueva-funcionalidad`
3. Commit sus cambios: `git commit -am 'Añadir nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Envíe un Pull Request
