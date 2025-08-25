import os
import dotenv
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pypdf import PdfReader

# Cargar variables de entorno primero
dotenv.load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no encontrado en variables de entorno")

semantic_chunker = SemanticChunker(OpenAIEmbeddings(model="text-embedding-3-large", api_key=OPENAI_API_KEY), breakpoint_threshold_type="percentile")

def chunk_text(document_path: str):
    """Lee un archivo PDF, extrae el texto y lo divide en chunks semánticos."""
    reader = PdfReader(document_path)
    text = "".join(page.extract_text() for page in reader.pages)
    return semantic_chunker.split_text(text)

def create_vector_store(chunks):
    # Usamos from_texts para crear el vector store desde una lista de strings
    vector_store = FAISS.from_texts(chunks, OpenAIEmbeddings(model="text-embedding-3-large", api_key=OPENAI_API_KEY))
    return vector_store

def search_vector_store(vector_store, query):
    results = vector_store.similarity_search(query)
    return results

def answer_user_query(user_question: str, vector_store):
    return vector_store.invoke(user_question)

if __name__ == "__main__":
    doc_path = r"C:\Users\eduar\Workspace\ZeroQ\agenteChilecompra\docs\anuario_estadistico_aduanas_2024.pdf"
    chunks = chunk_text(doc_path)
    vector_store = create_vector_store(chunks)
    
    user_question = "de que trata el documento y en qué moneda están los precios?"
    answer = search_vector_store(vector_store, user_question)
    print(answer)