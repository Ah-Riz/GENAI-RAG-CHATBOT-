import os
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import faiss
from dotenv import load_dotenv
load_dotenv()

def ingest_pdfs(pdf_dir = "data/pdfs"):
    model = SentenceTransformer(os.getenv("SENTENCE_TRANSFORMERS"))

    dimension = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatL2(dimension)

    metadata = []

    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            reader = PdfReader(os.path.join(pdf_dir, filename))
            text = ""
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                
                if not text:
                    continue

                chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
                for chunk in chunks:
                    embedding = model.encode(chunk)
                    embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)
                    index.add(embedding)
                    metadata.append({
                        "source": filename,
                        "page": page_num + 1,
                        "text": chunk
                    })
    faiss.write_index(index, "data/vector_store/uk_nhs_index.faiss")
    with open("data/vector_store/uk_nhs_index_metadata.json", "w") as f:
        json.dump(metadata, f)

if __name__ == "__main__":
    ingest_pdfs()