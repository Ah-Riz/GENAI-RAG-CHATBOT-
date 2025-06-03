import os
from dotenv import load_dotenv
import streamlit as st
import requests
import time
import json

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DOCUMENT_URL = "https://www.longtermplan.nhs.uk/wp-content/uploads/2019/08/nhs-long-term-plan-version-1.2.pdf"

st.set_page_config(
    page_title="UK NHS RAG Chatbot",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 UK NHS Long-term Plan RAG Chatbot")
st.caption(f"Using UK NHS 2019 [documents]({DOCUMENT_URL})")

def check_backend_health():
    """Check if backend is running and healthy"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "healthy", data
        return False, {"error": f"Backend returned status {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return False, {"error": "Cannot connect to backend"}
    except requests.exceptions.Timeout:
        return False, {"error": "Backend health check timed out"}
    except Exception as e:
        return False, {"error": f"Health check failed: {str(e)}"}

def wait_for_backend(max_retries=15):
    """Wait for backend to be ready"""
    for i in range(max_retries):
        is_healthy, status = check_backend_health()
        if is_healthy:
            return True, status
        
        with st.empty():
            st.info(f"⏳ Waiting for backend to start... ({i+1}/{max_retries})")
            time.sleep(2)
    
    return False, status

# Check backend status
with st.spinner("🔧 Checking backend status..."):
    is_healthy, backend_status = check_backend_health()
    
    if not is_healthy:
        st.warning("🚀 Backend is starting up, please wait...")
        is_healthy, backend_status = wait_for_backend()
        
        if not is_healthy:
            st.error(f"❌ Backend is not responding: {backend_status.get('error', 'Unknown error')}")
            st.info("Please refresh the page or contact support if the issue persists.")
            st.stop()

# Show backend status
if backend_status.get("documents_loaded", 0) > 0:
    st.success(f"✅ Backend ready! {backend_status['documents_loaded']} documents loaded.")
else:
    st.warning("⚠️ Backend is running but no documents are loaded.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello! I'm here to help you with questions about UK NHS policies. How can I assist you today?"}
    ]

# Display chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])
            if "source" in msg and msg["source"]:
                with st.expander("📚 Sources"):
                    for source in msg["source"]:
                        st.caption(f"• {source['source']}, Page: {source['page']}")

# Chat input
if prompt := st.chat_input("Ask about UK NHS policies..."):
    # Add user message
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Make request to backend
                response = requests.post(
                    f"{BACKEND_URL}/ask", 
                    json={"question": prompt}, 
                    timeout=60,
                    headers={"Content-Type": "application/json"}
                )
                
                # Check response status
                if response.status_code != 200:
                    error_msg = f"Backend error (HTTP {response.status_code})"
                    try:
                        error_detail = response.json()
                        error_msg += f": {error_detail.get('detail', 'Unknown error')}"
                    except:
                        error_msg += f": {response.text}"
                    
                    st.error(error_msg)
                    st.session_state["messages"].append({
                        "role": "assistant", 
                        "content": error_msg
                    })
                    st.stop()
                
                # Parse JSON response
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON response from backend: {str(e)}\nResponse: {response.text[:200]}..."
                    st.error(error_msg)
                    st.session_state["messages"].append({
                        "role": "assistant", 
                        "content": error_msg
                    })
                    st.stop()
                
                # Extract answer and sources
                if "error" in data:
                    answer = f"Backend Error: {data['error']}"
                    sources = []
                else:
                    answer = data.get("answer", "No answer found.")
                    sources = data.get("source", [])
                
                # Display answer
                st.write(answer)
                
                # Display sources
                if sources:
                    with st.expander("📚 Sources"):
                        for source in sources:
                            st.caption(f"• {source['source']}, Page: {source['page']}")
                
                # Add to chat history
                st.session_state["messages"].append({
                    "role": "assistant", 
                    "content": answer, 
                    "source": sources
                })
                
            except requests.exceptions.Timeout:
                error_msg = "⏰ Request timed out. The backend might be processing a large request."
                st.error(error_msg)
                st.session_state["messages"].append({"role": "assistant", "content": error_msg})
                
            except requests.exceptions.ConnectionError:
                error_msg = f"🔌 Cannot connect to backend at {BACKEND_URL}. Please check if the backend is running."
                st.error(error_msg)
                st.session_state["messages"].append({"role": "assistant", "content": error_msg})
                
            except Exception as e:
                error_msg = f"❌ Unexpected error: {str(e)}"
                st.error(error_msg)
                st.session_state["messages"].append({"role": "assistant", "content": error_msg})

# Sidebar with info
# with st.sidebar:
#     st.header("ℹ️ About")
#     st.write("This chatbot uses RAG (Retrieval-Augmented Generation) to answer questions about UK NHS policies.")
    
#     st.header("🔧 Backend Status")
#     if st.button("🔄 Refresh Status"):
#         st.rerun()
    
#     is_healthy, status = check_backend_health()
#     if is_healthy:
#         st.success("✅ Backend: Healthy")
#         st.info(f"📚 Documents: {status.get('documents_loaded', 0)}")
#     else:
#         st.error("❌ Backend: Unhealthy")
#         st.error(status.get('error', 'Unknown error'))
