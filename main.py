import os
import dotenv
import util.logger_config as logger_config


#logger
logger = logger_config.get_logger(__name__)
logger.info("Inicializando Programa")

#env variables
dotenv.load_dotenv()
APIKEY = os.environ.get("OPENAI_API_KEY")
if not APIKEY:
    logger.error("OPENAI_API_KEY no encontrado en variables de entorno")
    raise ValueError("OPENAI_API_KEY no encontrado en variables de entorno")
logger.info("APIKEY: ", APIKEY)

