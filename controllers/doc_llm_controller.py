from collections.abc import Collection
import os
import dotenv
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.weaviate import Weaviate
from langchain_weaviate.vectorstores import WeaviateVectorStore
from pypdf import PdfReader
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.config import Configure
from util.logger_config import get_logger

logger = get_logger(__name__)

# Cargar variables de entorno primero
dotenv.load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")
WEAVIATE_URL = os.environ.get("WEAVIATE_URL")

if not all([OPENAI_API_KEY, WEAVIATE_API_KEY, WEAVIATE_URL]):
    logger.error("Una o más variables de entorno (OPENAI, WEAVIATE) no están configuradas.")
    raise ValueError("Una o más variables de entorno (OPENAI, WEAVIATE) no están configuradas.")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=OPENAI_API_KEY)
semantic_chunker = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")

def chunk_text(document_path: str):
    """Lee un PDF, extrae texto y lo divide en chunks semánticos."""
    logger.info(f"Procesando documento: {document_path}")
    try:
        reader = PdfReader(document_path)
        text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
        if not text:
            logger.error(f"No se pudo extraer texto del documento: {document_path}")
            raise ValueError(f"No se pudo extraer texto del documento: {document_path}. El archivo puede ser una imagen o estar corrupto.")
        
        logger.debug("Dividiendo el texto en chunks semánticos.")
        text_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
        docs = text_splitter.create_documents([text])
        logger.info(f"Documento dividido en {len(docs)} chunks.")
        return docs
    except Exception as e:
        logger.error(f"Error al procesar el PDF {document_path}: {e}")
        raise

def get_weaviate_client():
    """Conecta al cluster de Weaviate Cloud."""
    logger.info("Conectando al cliente de Weaviate...")
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=WEAVIATE_URL,
            auth_credentials=Auth.api_key(WEAVIATE_API_KEY)
        )
        if not client.is_ready():
            logger.error("No se pudo conectar al cliente de Weaviate.")
            raise Exception("No se pudo conectar al cliente de Weaviate.")
        logger.info("Cliente de Weaviate conectado y listo.")
        return client
    except Exception as e:
        logger.error(f"Error al conectar con Weaviate: {e}")
        raise

def get_or_create_collection(client, index_name):
    """Obtiene la colección si existe, si no, la crea."""
    logger.debug(f"Verificando existencia de la colección '{index_name}'...")
    try:
        if not client.collections.exists(index_name):
            logger.info(f"Creando nueva colección '{index_name}'...")
            client.collections.create(
                name=index_name,
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                ],
                vectorizer_config=Configure.Vectorizer.text2vec_openai()
            )
            logger.info(f"Colección '{index_name}' creada exitosamente.")
        else:
            logger.info(f"Colección '{index_name}' ya existe.")
        return client.collections.get(index_name)
    except Exception as e:
        logger.error(f"Error al obtener o crear la colección '{index_name}': {e}")
        raise

def vectorize_documents(doc_path):
    """Vectoriza documentos y los añade a la colección."""
    logger.info(f"Vectorizando documentos de: {doc_path}")
    try:
        semantic_chunks = chunk_text(doc_path)
        logger.debug(f"Documento dividido en {len(semantic_chunks)} chunks para vectorización.")
        client = get_weaviate_client()
        vector_store = WeaviateVectorStore.from_documents(semantic_chunks, embeddings, client=client)
        logger.info("Documentos vectorizados y añadidos a la colección exitosamente.")
        return vector_store
    except Exception as e:
        logger.error(f"Error durante la vectorización de documentos: {e}")
        raise

def get_vector_stores(client):
    """Obtiene el vector store."""
    logger.info("Obteniendo todos los vector stores...")
    try:
        stores = client.collections.list_all()
        logger.info(f"Se encontraron {len(stores)} vector stores.")
        return stores
    except Exception as e:
        logger.error(f"Error al obtener los vector stores: {e}")
        raise

def search_documents(vector_store, query, k: int = 1):
    """Realiza una búsqueda en el vector store."""
    logger.info(f"Realizando búsqueda con k={k} para la consulta: '{query}'")
    try:
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        search_results = retriever.invoke(query)
        logger.info(f"Búsqueda completada. Se encontraron {len(search_results)} resultados.")
        return search_results
    except Exception as e:
        logger.error(f"Error durante la búsqueda de documentos: {e}")
        raise