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
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        print("Modelo de Lenguaje (LLM) inicializado correctamente.")   
        return llm
    except Exception as e:
        print(f"Ocurrió un error al inicializar o invocar el LLM: {e}")
        return None

def base_query():
    query = f""
    return query

if __name__ == "__main__":

    print("Test Orquestador")

    # 2. Inicializar el modelo de lenguaje (LLM)
    # Usamos ChatOpenAI que es ideal para modelos como gpt-3.5-turbo o gpt-4
    # - model: Especifica el modelo que quieres usar.
    # - temperature: Controla la "creatividad" del modelo. 0 es más determinista, 1 es más creativo.
    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        print("Modelo de Lenguaje (LLM) inicializado correctamente.")

        # 3. Prueba rápida para ver si funciona
        print("\n--- Realizando una prueba de invocación ---")
        respuesta = llm.invoke("Hola, ¿hwoami?")

        print(f"\nRespuesta del LLM: {respuesta.content}")

    except Exception as e:
        print(f"Ocurrió un error al inicializar o invocar el LLM: {e}")