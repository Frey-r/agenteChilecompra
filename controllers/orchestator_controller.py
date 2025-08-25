import os
import dotenv
from langchain_openai import ChatOpenAI
from controllers import doc_llm_controller, bd_llm_controller
from langchain_core.tools import Tool
from langchain.prompts import ChatPromptTemplate
from util.logger_config import get_logger
import json

logger = get_logger(__name__)

#env variables
dotenv.load_dotenv()
APIKEY = os.environ.get("OPENAI_API_KEY")
if not APIKEY:
    logger.error("OPENAI_API_KEY no encontrado en variables de entorno")
    raise ValueError("OPENAI_API_KEY no encontrado en variables de entorno")

def init_llm(model: str = "gpt-5"):
    try:
        llm = ChatOpenAI(model=model, temperature=0, api_key=APIKEY)
        logger.info("Modelo de Lenguaje (LLM) inicializado correctamente.")
        return llm
    except Exception as e:
        logger.error(f"Ocurrió un error al inicializar el LLM: {e}")
        return None

def documents_context():
    """Genera y guarda el contexto de los documentos vectorizados."""
    logger.info("Iniciando la generación de contexto de documentos.")
    client = doc_llm_controller.get_weaviate_client()
    context_file_path = os.path.join('bd', 'contexto.json')

    # Cargar contexto existente o inicializar uno nuevo
    try:
        with open(context_file_path, 'r', encoding='utf-8') as f:
            context_data = json.load(f)
        logger.debug("Archivo de contexto cargado exitosamente.")
    except (FileNotFoundError, json.JSONDecodeError):
        context_data = {}
        logger.debug("No se encontró archivo de contexto, se creará uno nuevo.")

    try:
        collections = doc_llm_controller.get_vector_stores(client)
        collection_names = [col.name for col in collections.values()]
        logger.info(f"Se encontraron las siguientes colecciones: {collection_names}")
    except Exception as e:
        logger.error(f"Error al obtener las colecciones de Weaviate: {e}")
        raise

    llm = init_llm()
    if not llm:
        logger.error("No se pudo inicializar el LLM. Abortando la generación de contexto.")
        return

    updated = False
    for name in collection_names:
        if name not in context_data:
            logger.info(f"Generando contexto para la colección: '{name}'")
            try:
                collection = client.collections.get(name)
                # Obtener todo el texto de la colección
                response = collection.query.fetch_objects(limit=1000) 
                full_text = " ".join([o.properties['text'] for o in response.objects])

                if not full_text.strip():
                    logger.warning(f"La colección '{name}' está vacía o no contiene texto.")
                    continue

                prompt = f"""
                Analiza el siguiente texto y genera un resumen conciso que describa su contenido principal.
                Texto: {full_text[:4000]} 
                """
                ai_response = llm.invoke(prompt)
                context_data[name] = ai_response.content
                logger.info(f"Contexto generado para '{name}': {ai_response.content[:100]}...")
                updated = True

            except Exception as e:
                logger.error(f"Error al procesar la colección '{name}': {e}")

    # Guardar el contexto actualizado si hubo cambios
    if updated:
        try:
            with open(context_file_path, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Archivo de contexto guardado en: {context_file_path}")
        except Exception as e:
            logger.error(f"Error al guardar el archivo de contexto: {e}")
    else:
        logger.info("No se generaron nuevos contextos, no se requiere actualización del archivo.")