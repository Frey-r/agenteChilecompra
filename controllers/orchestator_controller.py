import os
import dotenv
from langchain_openai import ChatOpenAI

#env variables
dotenv.load_dotenv()
APIKEY = os.environ.get("OPENAI_API_KEY")
if not APIKEY:
    raise ValueError("OPENAI_API_KEY no encontrado en variables de entorno")
print("APIKEY: ", APIKEY)

def init_llm():
    try:
        # Usamos un modelo más accesible como gpt-3.5-turbo
        llm = ChatOpenAI(model="gpt-5", temperature=0, api_key=APIKEY)
        print("Modelo de Lenguaje (LLM) inicializado correctamente.")
        return llm
    except Exception as e:
        print(f"Ocurrió un error al inicializar el LLM: {e}")
        return None

if __name__ == "__main__":
    print("--- Iniciando Agente de Inteligencia de Negocios ---")
    # 1. Inicializar el LLM
    llm_instance = init_llm()

    if llm_instance:
        print(llm_instance.invoke("hola").content)
    print("\n--- Proceso del Agente Finalizado ---")