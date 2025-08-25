import os
import dotenv
from langchain_openai import ChatOpenAI
from controllers import doc_llm_controller, bd_llm_controller
from langchain_core.tools import Tool
from langchain.prompts import ChatPromptTemplate
from util.logger_config import get_logger
import json
from sqlalchemy import create_engine
from partial_json_parser import loads

logger = get_logger(__name__)

#env variables
dotenv.load_dotenv()
APIKEY = os.environ.get("OPENAI_API_KEY")
DATABASE_URL = f"sqlite:///{os.environ.get('DATABASE_URL')}"
engine = create_engine(DATABASE_URL)

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

    return context_data

def user_query(user_question: str):
    logger.info(f"Recibida pregunta de usuario: '{user_question}'")
    try:
        llm = init_llm('gpt-5')
        if not llm:
            raise Exception("No se pudo inicializar el LLM para la consulta.")

        logger.debug("Obteniendo esquema de la base de datos...")
        bdd_schema = bd_llm_controller.get_db_schema(engine)
        logger.debug("Obteniendo contexto de documentos...")
        doc_context = documents_context()

        prompt_conocimiento = f"""Eres un asistente experto que responde preguntas sobre órdenes de compra del sector público de Chile.

        Tienes acceso a dos fuentes de información:
        1. Una base de datos con el siguiente esquema:
        ```json
        {json.dumps(bdd_schema, indent=4)}
        ```

        2. Un conjunto de documentos de apoyo con los siguientes contextos:
        ```json
        {json.dumps(doc_context, indent=4)}
        ```

        Basándote exclusivamente en esta información, responde donde está la información que necesito para responder a esta pregunta: {user_question}
        responde en formato json con la siguiente estructura:
        ```json
        {
            "base_de_datos": Boolean,
            "documentos":["collection_name"]
        }
        ```
        ejemplo:
        ```json
        {
            "base_de_datos": True,
            "documentos":["LangChain_4f9bea898c094ff6b5465f57ca978cf5","LangChain_e00aa9eee070450ba3aa403e453c696f"]
        }
        """
        logger.debug(f"Prompt construido para el LLM: {prompt_conocimiento[:500]}...")


        response_conocimiento = llm.invoke(prompt_conocimiento)
        jsoned_response_conocimiento = loads(response_conocimiento.content)

        client = doc_llm_controller.get_weaviate_client()

        db_data_str = "No se consultaron datos de la base de datos."
        if jsoned_response_conocimiento.get('base_de_datos', False):
            logger.info("Consultando la base de datos...")
            db_result_df, sql_query = bd_llm_controller.answer_user_query(llm, user_question)
            if db_result_df is not None and not db_result_df.empty:
                db_data_str = db_result_df.to_json(orient='records', indent=4)
            else:
                db_data_str = "La consulta a la base de datos no arrojó resultados."

        doc_data_str = "No se consultaron documentos."
        if jsoned_response_conocimiento.get('documentos') and len(jsoned_response_conocimiento['documentos']) > 0:
            logger.info("Consultando documentos...")
            response_documents = []
            for doc_name in jsoned_response_conocimiento['documentos']:
                try:
                    collection = client.collections.get(doc_name)
                    search_results = doc_llm_controller.search_documents(collection, user_question)
                    response_documents.append({doc_name: search_results})
                except Exception as e:
                    logger.error(f"Error al buscar en la colección {doc_name}: {e}")
            if response_documents:
                doc_data_str = json.dumps(response_documents, indent=4, default=str)


        final_prompt = f"""Eres un analista económico experto. Tu tarea es responder la pregunta del usuario basándote en los datos proporcionados.
        Sintetiza la información de la base de datos y de los documentos para dar una respuesta clara y concisa.

        **Pregunta del Usuario:**
        {user_question}

        **Datos de la Base de Datos (en formato JSON):**
        ```json
        {db_data_str}
        ```

        **Datos de los Documentos (Resultados de búsqueda semántica):**
        ```json
        {doc_data_str}
        ```

        **Respuesta Final:**
        """

        logger.info("Generando respuesta final con el agente sintetizador...")
        final_response = init_llm('gpt-5').invoke(final_prompt)
        logger.info("Respuesta generada por el LLM exitosamente.")
        return final_response.content

    except Exception as e:
        logger.error(f"Error al procesar la consulta del usuario: {e}")
        return "Lo siento, ocurrió un error al procesar tu pregunta. Por favor, intenta de nuevo más tarde."

    
    