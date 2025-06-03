FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory (if not exists)
RUN mkdir -p data/vector_store

# Expose ports
EXPOSE 8000 8501

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Start both services
CMD ["./start.sh"]