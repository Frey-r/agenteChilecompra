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

# Cargar variables de entorno primero
dotenv.load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")
WEAVIATE_URL = os.environ.get("WEAVIATE_URL")

if not all([OPENAI_API_KEY, WEAVIATE_API_KEY, WEAVIATE_URL]):
    raise ValueError("Una o más variables de entorno (OPENAI, WEAVIATE) no están configuradas.")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=OPENAI_API_KEY)
semantic_chunker = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")

def chunk_text(document_path: str):
    """Lee un PDF, extrae texto y lo divide en chunks semánticos."""
    reader = PdfReader(document_path)
    text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
    if not text:
        raise ValueError(f"No se pudo extraer texto del documento: {document_path}. El archivo puede ser una imagen o estar corrupto.")
    text_splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
    return text_splitter.create_documents([text])

def get_weaviate_client():
    """Conecta al cluster de Weaviate Cloud."""
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY)
    )
    if not client.is_ready():
        raise Exception("No se pudo conectar al cliente de Weaviate.")
    print("Cliente de Weaviate conectado y listo.")
    return client

def get_or_create_collection(client, index_name):
    """Obtiene la colección si existe, si no, la crea."""
    if not client.collections.exists(index_name):
        print(f"Creando nueva colección '{index_name}'...")
        client.collections.create(
            name=index_name,
            properties=[
                Property(name="text", data_type=DataType.TEXT),
            ],
            vectorizer_config=Configure.Vectorizer.text2vec_openai()
        )
        print("Colección creada.")
    else:
        print(f"Colección '{index_name}' ya existe.")
    return client.collections.get(index_name)

def vectorize_documents(doc_path):
    """Vectoriza documentos y los añade a la colección."""
    sematic_chunks = chunk_text(doc_path)
    texts = [doc.page_content for doc in sematic_chunks]
    print(f"Documento dividido en {len(texts)} chunks.")
    vector_store = WeaviateVectorStore.from_documents(sematic_chunks, embeddings, client=client)
    print(f"Chunks cargados exitosamente. Errores: {len(collection.batch.failed_objects)}")
    return vector_store

def get_vector_stores(client):
    """Obtiene el vector store."""
    return client.collections.list_all()

def search_documents(vector_store, query, k : int = 1):
    """Realiza una búsqueda en el vector store."""
    retriver = vector_store.as_retriever(search_kwargs={"k": k}) 
    search_results = retriver.invoke(query)
    return search_results



    