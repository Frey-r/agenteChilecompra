import util.logger_config as logger_config
from fastapi import FastAPI
from uvicorn import run

app = FastAPI()

logger = logger_config.get_logger(__name__)
logger.info("Inicializando agente")

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000)

