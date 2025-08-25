import os
import dotenv
import util.logger_config as logger_config
from fastapi import FastAPI
from uvicorn import run
from contextlib import asynccontextmanager
from api import routes as api_routes
from controllers import orchestator_controller

#logger
logger = logger_config.get_logger(__name__)
logger.info("Inicializando agente")

