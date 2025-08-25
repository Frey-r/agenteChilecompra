import os
import dotenv
import util.logger_config as logger_config
from fastapi import FastAPI
from uvicorn import run
from contextlib import asynccontextmanager
from api import routes as api_routes
from controllers import orchestator_controller

logger = logger_config.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación, incluyendo el cierre de conexiones."""
    logger.info("Servidor iniciado.")
    yield
    # Lógica de apagado
    logger.info("Cerrando la conexión con Weaviate...")
    #cerrar conección con weaviate
    orchestator_controller.weaviate_client.close()
    logger.info("Conexión con Weaviate cerrada.")

app = FastAPI(lifespan=lifespan)

# Incluir las rutas de la API
app.include_router(api_routes.router)

if __name__ == "__main__":
    logger.info("Iniciando servidor FastAPI en http://localhost:8000")
    run(app, host="0.0.0.0", port=8000)
