import os
import sys
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, UnstructuredPDFLoader, Docx2txtLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

# Load environment variables
load_dotenv()

def get_embeddings():
    """Initialize the same embedding model used in internal_knowledge.py"""
    api_key = os.getenv("API_4")    
    if not api_key:
        raise ValueError("API_4 environment variable not set (required for Google Embeddings)")
        
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=api_key
    )

def load_document(file_path: str):
    """Load a document based on its extension."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    
    print(f"Loading {file_path}...")
    
    if ext == '.pdf':
        try:
            print("Attempting to load PDF with UnstructuredPDFLoader...")
            loader = UnstructuredPDFLoader(file_path)
        except Exception as e:
            print(f"UnstructuredPDFLoader failed: {e}. Falling back to PyPDFLoader.")
            loader = PyPDFLoader(file_path)
            
    elif ext == '.docx':
        try:
            print("Attempting to load DOCX with UnstructuredWordDocumentLoader...")
            loader = UnstructuredWordDocumentLoader(file_path)
        except Exception as e:
            print(f"UnstructuredWordDocumentLoader failed: {e}. Falling back to Docx2txtLoader.")
            loader = Docx2txtLoader(file_path)
            
    elif ext == '.txt':
        loader = TextLoader(file_path, encoding='utf-8')
        
    elif ext == '.md':
        loader = UnstructuredMarkdownLoader(file_path)
        
    else:
        print(f"Warning: Unsupported extension {ext}, attempting to load as text.")
        loader = TextLoader(file_path, encoding='utf-8')
    
    return loader.load()

def ingest_file(file_path: str):
    """Main ingestion process."""
    try:
        # 1. Load Document
        docs = load_document(file_path)
        print(f"Loaded {len(docs)} pages/documents.")

        # 2. Split Text
        print("Splitting text into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        splits = text_splitter.split_documents(docs)
        print(f"Created {len(splits)} chunks.")

        # 3. Initialize Embeddings & Vector Store
        print("Initializing Embeddings...")
        embeddings = get_embeddings()
        
        index_name = "boundless-alder"
        print(f"Target Pinecone Index: {index_name}")

        # 4. Upsert to Pinecone
        print("Upserting vectors to Pinecone...")
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not pinecone_api_key:
             raise ValueError("PINECONE_API_KEY environment variable not set")

        PineconeVectorStore.from_documents(
            documents=splits,
            embedding=embeddings,
            index_name=index_name,
            pinecone_api_key=pinecone_api_key
        )
        
        print("✅ Ingestion successfully completed!")
        
    except Exception as e:
        print(f"❌ Error during ingestion: {str(e)}")

# CLI Entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python ingest_docs.py <path_to_file>")
        print("Example: python ingest_docs.py ./data/my_document.pdf\n")
    else:
        target_file = sys.argv[1]
        # Handle relative paths
        if not os.path.isabs(target_file):
            target_file = os.path.abspath(target_file)
            
        ingest_file(target_file)
