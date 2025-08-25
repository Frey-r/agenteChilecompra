import os
import dotenv
from langchain_openai import ChatOpenAI
from controllers import doc_llm_controller, bd_llm_controller
from langchain_core.tools import Tool
from langchain.prompts import ChatPromptTemplate

#env variables
dotenv.load_dotenv()
APIKEY = os.environ.get("OPENAI_API_KEY")
if not APIKEY:
    raise ValueError("OPENAI_API_KEY no encontrado en variables de entorno")
print("APIKEY: ", APIKEY)

def init_llm(model: str = "gpt-5"):
    try:
        # Usamos un modelo más accesible como gpt-3.5-turbo
        llm = ChatOpenAI(model=model, temperature=0, api_key=APIKEY)
        print("Modelo de Lenguaje (LLM) inicializado correctamente.")
        return llm
    except Exception as e:
        print(f"Ocurrió un error al inicializar el LLM: {e}")
        return None

