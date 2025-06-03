import os
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import numpy as np
import json
from dotenv import load_dotenv
load_dotenv()

def ingest_pdfs(pdf_dir = "data/pdfs"):
    model = SentenceTransformer(os.getenv("SENTENCE_TRANSFORMERS"))
    vector_store = []
    metadata = []

    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            reader = PdfReader(os.path.join(pdf_dir, filename))
            text = ""
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
                for chunk in chunks:
                    embedding = model.encode(chunk).tolist()
                    vector_store.append(embedding)
                    metadata.append({
                        "source": filename,
                        "page": page_num + 1,
                        "text": chunk
                    })
    vector_store = np.array(vector_store)
    with open("data/vector_store/uk_nhs_index.json", "w") as f:
        json.dump({"vectors": vector_store.tolist(), "metadata": metadata}, f)

if __name__ == "__main__":
    ingest_pdfs()