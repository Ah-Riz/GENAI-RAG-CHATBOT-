import os
import numpy as np
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
import requests
import json
import traceback


class RAGSystem:
    def __init__(self):
        model_name = os.getenv("SENTENCE_TRANSFORMERS")
        self.model = SentenceTransformer(model_name)
        
        with open("data/vector_store/uk_nhs_index.json", "r") as f:
            data = json.load(f)
            self.vector_store = np.array(data["vectors"])
            self.metadata = data["metadata"]
            
    def find_similar(self, query, k=2):
        score = np.dot(self.vector_store, query)
        top_indices = np.argsort(score)[-k:][::-1]
        return [self.metadata[i] for i in top_indices]
        
    def encode_query(self, question):
        return self.model.encode(question).tolist()

app = FastAPI()
RAGSystem = RAGSystem()

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

class Query(BaseModel):
    question: str

def query_hf(payload):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def extract_answer(response):
    try:
        if not response:
            return "No response received from AI model"
        
        if isinstance(response, str):
            if "Answer:" in response:
                return response.split("Answer:")[-1].strip()
            return response.strip()
        
        if isinstance(response, dict):
            if "error" in response:
                return f"AI model error: {response['error']}"
            if "generated_text" in response:
                generated_text = response["generated_text"]
            else:
                return "No generated text in response"
        
        elif isinstance(response, list) and len(response) > 0:
            first_item = response[0]
            if isinstance(first_item, dict) and "generated_text" in first_item:
                generated_text = first_item["generated_text"]
            elif isinstance(first_item, str):
                generated_text = first_item
            else:
                return f"Unexpected list item format: {type(first_item)}"
        else:
            return f"Unexpected response format: {type(response)}"
        
        # Extract answer after "Answer:" delimiter
        if "Answer:" in generated_text:
            return generated_text.split("Answer:")[-1].strip()
        else:
            return generated_text.strip()
    except Exception as e:
        return f"Error processing response: {str(e)}"


@app.post("/ask")
async def ask(query: Query):
    try:
        if not HF_TOKEN:
            return {"error": "Hugging Face token is not set in environment variables."}
        query_embed = RAGSystem.encode_query(query.question)
        similar_docs = RAGSystem.find_similar(query_embed)
        context = "\n".join([f"Source: {doc['source']}, Page: {doc['page']}\n{doc['text']}" for doc in similar_docs])

        prompt = f"""Answer using ONLY the NHS/GOV documents below:
        
        {context}
        
        Question: {query.question}
        Answer:"""
        
        answer = extract_answer(query_hf({"inputs": prompt, "parameters": {"max_new_tokens": 512}}))
        return {"answer": answer, "source": [{"source": doc["source"], "page": doc["page"]} for doc in similar_docs]}
    except Exception as e:
        traceback.print_exc()
        return {"error": f"Server error: {str(e)}", "source": []}

@app.get("/health")
async def health_check():
    try:
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.get("/env-test")
async def env_test():
    return {
        "HF_TOKEN": "***" if os.getenv("HF_TOKEN") else "Not set",
        "SENTENCE_TRANSFORMERS": os.getenv("SENTENCE_TRANSFORMERS"),
        "BACKEND_URL": os.getenv("BACKEND_URL")
    }