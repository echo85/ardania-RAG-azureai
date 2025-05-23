import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Path to the directory where you cloned the repo
REPO_PATH = "ardania-md"  # Change this if you cloned it elsewhere
# Directory to save the Chroma database
PERSIST_DIRECTORY = "chroma_db_ardania"
# Choose your embedding model (use a strong multilingual one)
# Recommended: "intfloat/multilingual-e5-large", "BAAI/bge-m3"
MODEL_NAME = "jeffh/intfloat-multilingual-e5-large:f16"
OLAMA_API_KEY = os.environ.get("OLAMA_API_KEY")
OLAMA_API_URL = os.environ.get("OLAMA_API_URL")
# Chunking parameters (experiment with these)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
# --- End Configuration ---

# --- Check if repo path exists ---
if not os.path.exists(REPO_PATH):
    print(f"Error: Repository path '{REPO_PATH}' not found.")
    print(
        "Please clone the repository first: git clone https://github.com/jacklake-tm/ardania-md.git"
    )
    exit()

print(f"Loading Markdown documents from: {REPO_PATH}")

# --- Load Markdown Documents ---
# Use DirectoryLoader to load all .md files recursively
# UnstructuredMarkdownLoader is generally good for parsing Markdown structure
loader = DirectoryLoader(
    REPO_PATH,
    glob="**/*.md",  # Pattern to match only markdown files
    loader_cls=TextLoader,
    show_progress=True,
    use_multithreading=True,  # Can speed up loading
)

documents = loader.load()

if not documents:
    print("No markdown documents found. Check the REPO_PATH and glob pattern.")
    exit()
else:
    print(f"Loaded {len(documents)} documents.")

# --- Split Documents into Chunks ---
print(
    f"Splitting documents into chunks (size: {CHUNK_SIZE}, overlap: {CHUNK_OVERLAP})..."
)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    # Consider Markdown-specific separators if needed, but recursive usually works well
    # separators=["\n\n", "\n", " ", ""],
    length_function=len,
)
docs_split = text_splitter.split_documents(documents)
print(f"Split into {len(docs_split)} chunks.")

# --- Initialize Embedding Model ---
print(f"Initializing embedding model: {MODEL_NAME}")

heders = headers = {
    "Authorization": f"Bearer {OLAMA_API_KEY}",
}
embeddings = OllamaEmbeddings(
    model=MODEL_NAME,
    base_url=OLAMA_API_URL,
    client_kwargs={"headers": headers},
)

# --- Create and Persist Chroma Vector Store ---
print(f"Creating Chroma vector store in: {PERSIST_DIRECTORY}")

# This will embed the chunks and store them in Chroma.
# It will save the index to the PERSIST_DIRECTORY.
vector_store = Chroma.from_documents(
    documents=docs_split,
    embedding=embeddings,
    persist_directory=PERSIST_DIRECTORY,
    # Optional: Add IDs if you want more control, otherwise Chroma generates them
    # ids=[f"chunk_{i}" for i in range(len(docs_split))]
    collection_metadata={"hnsw:space": "cosine"},  # Explicitly set cosine distance
)

print("----- Indexing Complete -----")
print(f"Vector store created and persisted at: {PERSIST_DIRECTORY}")
print(f"Number of vectors stored: {vector_store._collection.count()}")
