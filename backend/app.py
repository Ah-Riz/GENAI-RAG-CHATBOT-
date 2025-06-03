import os
import numpy as np
from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
import requests
import json
import traceback
from dotenv import load_dotenv

load_dotenv()

class RAGSystem:
    def __init__(self):
        try:
            model_name = os.getenv("SENTENCE_TRANSFORMERS", "all-MiniLM-L6-v2")
            print(f"Loading model: {model_name}")
            self.model = SentenceTransformer(model_name, cache_folder="/tmp/.cache/sentence_transformers")
            
            # Check if vector store exists
            vector_store_path = "data/vector_store/uk_nhs_index.json"
            if os.path.exists(vector_store_path):
                with open(vector_store_path, "r") as f:
                    data = json.load(f)
                    self.vector_store = np.array(data["vectors"])
                    self.metadata = data["metadata"]
                print(f"Loaded {len(self.metadata)} documents from vector store")
            else:
                print("Warning: Vector store not found, creating empty store")
                self.vector_store = np.array([])
                self.metadata = []
        except Exception as e:
            print(f"Error initializing RAG system: {e}")
            traceback.print_exc()
            raise
    
    def find_similar(self, query, k=2):
        if len(self.vector_store) == 0:
            return []
        
        try:
            query = np.array(query).reshape(1, -1)
            scores = np.dot(self.vector_store, query.T).flatten()
            top_indices = np.argsort(scores)[-k:][::-1]
            return [self.metadata[i] for i in top_indices if i < len(self.metadata)]
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
        
    def encode_query(self, question):
        try:
            return self.model.encode(question).tolist()
        except Exception as e:
            print(f"Error encoding query: {e}")
            return []

app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# Initialize RAG system
try:
    rag_system = RAGSystem()
    print("RAG system initialized successfully")
except Exception as e:
    print(f"Failed to initialize RAG system: {e}")
    rag_system = None

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

class Query(BaseModel):
    question: str

def query_hf(payload):
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 503:
            return {"error": "Model is loading, please try again in a few minutes"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def extract_answer(response):
    try:
        if not response:
            return "No response received from AI model"
        
        if isinstance(response, dict) and "error" in response:
            return f"AI model error: {response['error']}"
        
        generated_text = ""
        
        if isinstance(response, str):
            generated_text = response
        elif isinstance(response, dict):
            generated_text = response.get("generated_text", "")
        elif isinstance(response, list) and len(response) > 0:
            first_item = response[0]
            if isinstance(first_item, dict):
                generated_text = first_item.get("generated_text", "")
            elif isinstance(first_item, str):
                generated_text = first_item
        
        if not generated_text:
            return "No text generated"
        
        # Extract answer after "Answer:" delimiter
        if "Answer:" in generated_text:
            return generated_text.split("Answer:")[-1].strip()
        else:
            return generated_text.strip()
            
    except Exception as e:
        return f"Error processing response: {str(e)}"

@app.get("/")
async def root():
    return {"message": "RAG Chatbot API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    try:
        status = "healthy" if rag_system is not None else "unhealthy"
        return {
            "status": status,
            "message": "Backend is running",
            "rag_initialized": rag_system is not None,
            "documents_loaded": len(rag_system.metadata) if rag_system else 0
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/ask")
async def ask(query: Query):
    try:
        # Validate inputs
        if not query.question or not query.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        if not HF_TOKEN:
            raise HTTPException(status_code=500, detail="Hugging Face token is not configured")
        
        if not rag_system:
            raise HTTPException(status_code=500, detail="RAG system is not initialized")
        
        # Process query
        print(f"Processing query: {query.question}")
        
        query_embed = rag_system.encode_query(query.question)
        if not query_embed:
            raise HTTPException(status_code=500, detail="Failed to encode query")
        
        similar_docs = rag_system.find_similar(query_embed)
        
        if not similar_docs:
            context = "No relevant documents found."
            sources = []
        else:
            context = "\n".join([f"Source: {doc.get('source', 'Unknown')}, Page: {doc.get('page', 'Unknown')}\n{doc.get('text', '')}" for doc in similar_docs])
            sources = [{"source": doc.get("source", "Unknown"), "page": doc.get("page", "Unknown")} for doc in similar_docs]

        prompt = f"""Answer using ONLY the NHS/GOV documents below:
        
        {context}
        
        Question: {query.question}
        Answer:"""
        
        # Query Hugging Face API
        hf_response = query_hf({
            "inputs": prompt, 
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.7,
                "do_sample": True
            }
        })
        
        answer = extract_answer(hf_response)
        
        return {
            "answer": answer,
            "source": sources,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /ask endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
