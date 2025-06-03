# Start FastAPI in background
uvicorn backend.app:app --host 0.0.0.0 --port 8000 &

# Start Streamlit in foreground
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0