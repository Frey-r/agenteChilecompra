from fastapi import APIRouter
from pydantic import BaseModel
from controllers import orchestator_controller
import util.logger_config as logger_config

router = APIRouter()
logger = logger_config.get_logger(__name__)

# Modelo para la entrada de la consulta
class QueryRequest(BaseModel):
    question: str

# Inicializar el LLM y el orquestador
llm = orchestator_controller.init_llm()
orchestrator = orchestator_controller.create_orchestrator_agent(llm, orchestator_controller.tools)

@router.post("/query/")
def handle_query(request: QueryRequest):
    """Recibe una pregunta, la procesa con el orquestador y devuelve la respuesta."""
    logger.info(f"Recibida consulta: '{request.question}'")
    try:
        response = orchestrator.invoke({"input": request.question})
        logger.info(f"Respuesta generada: {response['output']}")
        return {"answer": response['output']}
    except Exception as e:
        logger.error(f"Error al procesar la consulta: {e}")
        return {"error": "Ocurrió un error al procesar la consulta."}
