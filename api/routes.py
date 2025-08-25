from fastapi import APIRouter
from pydantic import BaseModel
from controllers import orchestator_controller
from controllers import doc_llm_controller
import api.requests as requests
import base64
import util.logger_config as logger_config

router = APIRouter()
logger = logger_config.get_logger(__name__)



# Inicializar el LLM y el orquestador
llm = orchestator_controller.init_llm()

@router.post("/ask")
async def handle_query(request: requests.AskRequest):
    """Recibe una pregunta, la procesa con el orquestador y devuelve la respuesta."""
    logger.info(f"Recibida consulta: '{request.question}'")
    try:
        response = orchestator_controller.user_query(request.question)
        logger.info(f"Respuesta generada: {response['output']}")
        return {"answer": response['output']}
    except Exception as e:
        logger.error(f"Error al procesar la consulta: {e}")
        return {"error": "Ocurrió un error al procesar la consulta."}

@router.post("/documents/upload")
async def upload_document(request: requests.DocumentRequest):
    """Recibe un documento PDF y lo procesa con el orquestador."""
    logger.info("Recibido documento PDF")
    try:
        pdf_data = base64.b64decode(request.pdf)
        with open(f"docs/{request.name}.pdf", "wb") as f:
            f.write(pdf_data)
        doc_llm_controller.vectorize_documents(f"docs/{request.name}.pdf")
        return {"message": "Documento procesado exitosamente"}
    except Exception as e:
        logger.error(f"Error al procesar el documento: {e}")
        return {"error": "Ocurrió un error al procesar el documento."}