FROM python:3.12-slim

ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/app/cache
ENV HF_HOME=/app/cache
ENV TORCH_HOME=/app/cache
ENV XDG_CACHE_HOME=/app/cache

WORKDIR /app
RUN mkdir -p /app/cache && chmod 777 /app/cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Pre-download model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder='/app/cache')"

# Set environment variables

EXPOSE 8000 8501

# Run the main app
CMD ["python", "app.py"]