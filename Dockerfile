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
COPY start.sh .

# Make script executable
RUN chmod +x start.sh
RUN dos2unix start.sh && chmod +x start.sh

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Run the ingestion script first, then start the backend
CMD ["./start.sh"]