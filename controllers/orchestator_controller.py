import os
import dotenv
from langchain_openai import ChatOpenAI

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


# Inicializar clientes y retrievers una sola vez
weaviate_client = doc_llm_controller.get_weaviate_client()
doc_retriever = doc_llm_controller.get_retriever(weaviate_client, "AnuarioAduanas")
sql_agent_executor = bd_llm_controller.get_sql_agent_executor()

# Definir las herramientas que el orquestador puede usar
tools = [
    Tool(
        name="DocumentSearch",
        func=doc_retriever.invoke,
        description="Útil para responder preguntas sobre el contenido de documentos PDF, como el anuario estadístico de aduanas."
    ),
    Tool(
        name="DatabaseQuery",
        func=sql_agent_executor.invoke,
        description="Útil para responder preguntas que requieren consultar una base de datos sobre datos de negocio, licitaciones o inteligencia de mercado."
    ),
]

def create_orchestrator_agent(llm, tools):
    """Crea el agente orquestador que decide qué herramienta usar."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Eres un asistente inteligente que enruta las preguntas del usuario a la herramienta correcta. Analiza la pregunta y elige la mejor herramienta."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    llm = init_llm()
    orchestrator = create_orchestrator_agent(llm, tools)

    # Ejemplo de enrutamiento
    user_query_doc = "¿De qué trata el anuario de aduanas?"
    user_query_db = "¿Cuál es el monto total de las 5 licitaciones más grandes?"

    print(f"\n--- Consultando al orquestador sobre el documento ---")
    response_doc = orchestrator.invoke({"input": user_query_doc})
    print(f"Respuesta: {response_doc['output']}")

    print(f"\n--- Consultando al orquestador sobre la base de datos ---")
    response_db = orchestrator.invoke({"input": user_query_db})
    print(f"Respuesta: {response_db['output']}")

    weaviate_client.close()
    print("\n--- Proceso del Agente Finalizado ---")