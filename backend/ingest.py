import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def ingest_pdfs():
    loaders = [PyPDFLoader(f"data/pdfs/{f}") for f in os.listdir("data/pdfs")]
    docs = [doc for loader in loaders for doc in loader.load()]
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local("data/vector_store/uk_nhs_index")

if __name__ == "__main__":
    ingest_pdfs()