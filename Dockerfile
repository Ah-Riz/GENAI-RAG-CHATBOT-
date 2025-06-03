FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directories
RUN mkdir -p /tmp/.cache /tmp/.streamlit /app/data/vector_store

# Set environment variables
ENV PYTHONPATH=/app
ENV HF_HOME=/tmp/.cache/huggingface
ENV TRANSFORMERS_CACHE=/tmp/.cache/transformers
ENV STREAMLIT_CONFIG_DIR=/tmp/.streamlit
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8000 8501

# Run the main app
CMD ["python", "app.py"]


CMD ["curl", "-I", "http://localhost:8000/health"]