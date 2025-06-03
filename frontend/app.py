import os
from dotenv import load_dotenv
import streamlit as st
import requests

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
DOCUMEN_URL = "https://www.longtermplan.nhs.uk/wp-content/uploads/2019/08/nhs-long-term-plan-version-1.2.pdf"

st.title("UK NHS Longterm Plan RAG Chatbot")
st.caption("Using Mistral-7B and UK NHS 2019 [documents](%s)" % DOCUMEN_URL)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
        if "source" in msg:
            st.caption("Source: ")
            for source in msg["source"]:
                st.caption(f"- {source['source']}, Page: {source['page']}")
    else:
        st.chat_message("assistant").write(msg["content"])

if prompt := st.chat_input("Ask about UK NHS policies:"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Thinking..."):
        try:
            if not BACKEND_URL:
                raise ValueError("BACKEND_URL environment variable is not set")
            
            response = requests.post(f"{BACKEND_URL}/ask", json={"question": prompt}, timeout=30)
            response.raise_for_status()

            data = response.json()
            
            if "error" in data:
                answer = f"BACKEND Error: {data['error']}"
                sources = []
            else:
                answer = data.get("answer", "No answer found.")
                sources = data.get("source", [])
        except requests.exceptions.Timeout:
            answer = "Error: Request timed out. The backend might be processing a large request."
            sources = []
        except requests.exceptions.ConnectionError:
            answer = f"Error: Cannot connect to backend at {BACKEND_URL}. Make sure the backend is running."
            sources = []
        except requests.exceptions.HTTPError as e:
            answer = f"Error: HTTP {e.response.status_code} - {e.response.text}"
            sources = []
        except requests.exceptions.RequestException as e:
            answer = f"Error: Request failed - {str(e)}"
            sources = []
        except ValueError as e:
            answer = f"Configuration Error: {str(e)}"
            sources = []
        except Exception as e:
            answer = f"Unexpected Error: {str(e)}"
            sources = []

    st.session_state["messages"].append({"role": "assistant", "content": answer, "source": sources})
    st.chat_message("assistant").write(answer)
    
    if sources:
        st.caption("Sources:")
        for source in sources:
            st.caption(f"- {source['source']}, Page: {source['page']}")