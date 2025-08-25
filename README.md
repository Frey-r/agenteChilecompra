# Agente Chilecompra

Este proyecto es un asistente de IA diseñado para responder preguntas complejas utilizando datos de órdenes de compra de Chilecompra. El agente puede consultar tanto una base de datos relacional estructurada como una base de datos vectorial con documentos no estructurados (PDFs) para proporcionar respuestas precisas.

## Finalidad

El objetivo principal de este agente es facilitar el acceso y análisis de la información de compras públicas de Chile. Permite a los usuarios realizar consultas en lenguaje natural, que el sistema traduce a consultas SQL para la base de datos o a búsquedas semánticas en documentos, abstrayendo la complejidad técnica y entregando respuestas claras y directas.

## Arquitectura

El sistema está construido sobre una arquitectura de microservicios en Python, utilizando FastAPI para la capa de API. La lógica de negocio está separada en controladores especializados.

-   **API (`api/`):** Expone los endpoints para interactuar con el agente.
    -   `POST /ask`: Recibe una pregunta del usuario.
    -   `POST /documents/upload`: Permite cargar documentos PDF para ser procesados y vectorizados.
-   **Controladores (`controllers/`):** Contienen la lógica principal.
    -   `orchestator_controller.py`: Actúa como el cerebro del sistema. Recibe la pregunta del usuario y, utilizando un LLM, decide qué herramienta usar: el consultor de base de datos o el buscador de documentos.
    -   `bd_llm_controller.py`: Gestiona la interacción con la base de datos relacional (SQLite). Traduce la pregunta del usuario a un objeto JSON que se usa para construir una consulta SQL segura con SQLAlchemy.
    -   `doc_llm_controller.py`: Maneja el pipeline de RAG (Retrieval-Augmented Generation). Procesa los PDFs, los divide en chunks semánticos, genera embeddings con OpenAI y los almacena en una base de datos vectorial Weaviate.
-   **Almacenamiento de Datos:**
    -   **Base de Datos Relacional (`bd/`):** Almacena datos estructurados de Chilecompra en formato SQLite.
    -   **Base de Datos Vectorial:** Utiliza Weaviate para almacenar los embeddings de los documentos y realizar búsquedas de similitud.
    -   **Documentos (`docs/`):** Carpeta donde se guardan los PDFs subidos.

## Implementación

-   **Backend:** Python
-   **Framework API:** FastAPI
-   **Orquestación LLM:** LangChain
-   **Modelos de Lenguaje:** OpenAI (para embeddings y razonamiento)
-   **Base de Datos Relacional:** SQLAlchemy con SQLite
-   **Base de Datos Vectorial:** Weaviate
-   **Gestión de Dependencias:** Poetry

## Uso

### 1. Configuración del Entorno

Clona el repositorio y crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```
OPENAI_API_KEY="TU_API_KEY_DE_OPENAI"
WEAVIATE_URL="TU_URL_DE_WEAVIATE"
WEAVIATE_API_KEY="TU_API_KEY_DE_WEAVIATE"
DATABASE_URL="bd/chilecompra.db"
```

### 2. Instalación de Dependencias

Asegúrate de tener Poetry instalado y ejecuta:

```bash
poetry install
```

### 3. Iniciar el Servidor

Para iniciar la aplicación, ejecuta:

```bash
poetry run python main.py
```

El servidor estará disponible en `http://localhost:8000`.

### 4. Endpoints

-   **Hacer una pregunta:**
    Envía una petición `POST` a `http://localhost:8000/ask` con un JSON como el siguiente:
    ```json
    {
      "question": "¿Cuál es el proveedor con el mayor monto total en órdenes de compra?"
    }
    ```

-   **Subir un documento:**
    Envía una petición `POST` a `http://localhost:8000/documents/upload` con un JSON que contenga el nombre del archivo y el contenido del PDF en base64:
    ```json
    {
      "name": "nombre_del_archivo",
      "pdf": "CONTENIDO_EN_BASE64"
    }
    ```