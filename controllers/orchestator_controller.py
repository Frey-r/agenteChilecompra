import os
import dotenv
import util.logger_config as logger_config
from langchain_openai import ChatOpenAI


#logger
logger = logger_config.get_logger(__name__)
logger.info("Inicializando Orquestador")

#env variables
dotenv.load_dotenv()
APIKEY = os.environ.get("OPENAI_API_KEY")
if not APIKEY:
    logger.error("OPENAI_API_KEY no encontrado en variables de entorno")
    raise ValueError("OPENAI_API_KEY no encontrado en variables de entorno")
logger.info("APIKEY: ", APIKEY)

if __name__ == "__main__":
    logger.debug("Test Orquestador")

    # 2. Inicializar el modelo de lenguaje (LLM)
    # Usamos ChatOpenAI que es ideal para modelos como gpt-3.5-turbo o gpt-4
    # - model: Especifica el modelo que quieres usar.
    # - temperature: Controla la "creatividad" del modelo. 0 es más determinista, 1 es más creativo.
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        logger.debug("Modelo de Lenguaje (LLM) inicializado correctamente.")

        # 3. Prueba rápida para ver si funciona
        logger.debug("\n--- Realizando una prueba de invocación ---")
        respuesta = llm.invoke("Hola, ¿hwoami?")

        logger.debug(f"\nRespuesta del LLM: {respuesta.content}")

    except Exception as e:
        logger.error(f"Ocurrió un error al inicializar o invocar el LLM: {e}")