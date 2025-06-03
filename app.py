import subprocess
import sys
import time
import os

# Set environment variables
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
os.environ['HF_HOME'] = '/tmp/.cache/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/tmp/.cache/transformers'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
os.environ['HF_HOME'] = '/tmp/.cache/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/tmp/.cache/transformers'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/tmp/.cache/sentence_transformers'
os.environ['STREAMLIT_CONFIG_DIR'] = '/tmp/.streamlit'

def main():
    # Start backend
    backend = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "backend.app:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ])
    
    # Wait for backend to start
    time.sleep(10)
    
    # Start frontend
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "frontend/app.py", 
        "--server.port", "8501", 
        "--server.address", "0.0.0.0"
    ])

if __name__ == "__main__":
    main()
