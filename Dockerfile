FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port 8000", "sleep 15","streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"]