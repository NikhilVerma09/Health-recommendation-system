import streamlit as st
import requests
import pandas as pd
import time
import json
from datetime import datetime

# URL of our central "Broker" API
BROKER_API_URL = "http://127.0.0.1:8000"

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Hospital Chat")

# --- Helper Functions ---
@st.cache_data(ttl=1) # Cache for 1 second
def get_hospital_list():
    try:
        r = requests.get(f"{BROKER_API_URL}/api/hospitals")
        if r.status_code == 200:
            return r.json()
        return []
    except requests.ConnectionError:
        return []

def fetch_chat_history(thread_id):
    try:
        r = requests.get(f"{BROKER_API_URL}/api/chat-history/{thread_id}")
        if r.status_code == 200:
            return r.json()["messages"]
        return []
    except:
        return [{"role": "system", "content": "Error fetching history.", "timestamp": ""}]

def fetch_broadcast_replies(broadcast_id):
    try:
        r = requests.get(f"{BROKER_API_URL}/api/broadcast-replies/{broadcast_id}")
        if r.status_code == 200:
            return r.json()
        return {}
    except:
        return {"error": "Could not connect to broker."}

def format_timestamp(iso_string):
    """Helper to make timestamps prettier."""
    try:
        return datetime.fromisoformat(iso_string).strftime('%Y-%m-%d %H:%M')
    except:
        return ""

def display_message_content(content_string):
    """Tries to show content as JSON, falls back to plain text."""
    try:
        # Try to format as JSON
        content_data = json.loads(content_string)
        st.json(content_data)
    except (json.JSONDecodeError, TypeError):
        # Otherwise, just show as text
        st.markdown(content_string)

# --- Main App ---
st.title("🏥 Patient <> Hospital Chat System")
hospitals = get_hospital_list()

if not hospitals:
    st.error("❌ **Broker API is Offline!**")
    st.markdown("Please make sure the broker is running. Run in your terminal:")
    st.code("uvicorn broker_api:app --reload --port 8000", language="bash")
    st.stop()

# --- App Tabs ---
tab1, tab2 = st.tabs(["💬 Specific Chat", "📡 Broadcast to All"])

# --- TAB 1: Specific Chat ---
with tab1:
    st.header("Chat with a specific hospital")
    
    hospital_name = st.selectbox(
        "Select Hospital", 
        [h["name"] for h in hospitals], 
        key="specific_chat_select",
        index=None,
        placeholder="-- Select a hospital --"
    )

    if hospital_name:
        # Initialize chat history in session state
        if f"chat_thread_id_{hospital_name}" not in st.session_state:
            st.session_state[f"chat_thread_id_{hospital_name}"] = None

        thread_id = st.session_state[f"chat_thread_id_{hospital_name}"]

        # Chat message display area
        chat_container = st.container(height=400, border=True)
        if thread_id:
            messages = fetch_chat_history(thread_id)
            for msg in messages:
                with chat_container.chat_message(msg["role"]):
                    st.markdown(f"*{format_timestamp(msg['timestamp'])}*")
                    display_message_content(msg["content"])

        # Chat input
        if prompt := st.chat_input("What is your question?"):
            try:
                payload = {
                    "hospital_name": hospital_name,
                    "thread_id": thread_id,
                    "message": prompt
                }
                r = requests.post(f"{BROKER_API_URL}/api/chat", json=payload)
                
                if r.status_code == 200:
                    if not thread_id:
                        st.session_state[f"chat_thread_id_{hospital_name}"] = r.json().get("thread_id")
                    st.rerun()
                else:
                    st.error(f"Error sending message: {r.json().get('detail')}")
            except Exception as e:
                st.error(f"Failed to connect to broker: {e}")
    else:
        st.info("Select a hospital to begin chatting.")

# --- TAB 2: Broadcast to All ---
with tab2:
    st.header("Broadcast a message to all hospitals")
    st.warning("Hospitals will reply individually. Replies may take time.", icon="⏳")

    broadcast_msg = st.text_area("Your broadcast message:", key="broadcast_input")
    
    if st.button("Send to All"):
        if not broadcast_msg:
            st.error("Please enter a message to broadcast.")
        else:
            try:
                payload = {"message": broadcast_msg}
                r = requests.post(f"{BROKER_API_URL}/api/broadcast", json=payload)
                if r.status_code == 200:
                    st.session_state.broadcast_id = r.json().get("broadcast_id")
                    st.success(f"Broadcast sent! Your ID is: {st.session_state.broadcast_id}")
                    st.balloons()
                else:
                    st.error(f"Error from broker: {r.json().get('detail')}")
            except Exception as e:
                st.error(f"Failed to connect to broker: {e}")

    if "broadcast_id" in st.session_state:
        st.markdown("---")
        st.subheader("Check Broadcast Replies")
        
        if st.button("Refresh Replies"):
            broadcast_id = st.session_state.broadcast_id
            replies = fetch_broadcast_replies(broadcast_id)
            
            if not replies:
                st.info("No replies received yet.")
            else:
                st.success(f"Received replies from {len(replies)} hospital(s)!")
                for hospital, reply_list in replies.items():
                    with st.expander(f"Replies from {hospital} ({len(reply_list)} messages)"):
                        for msg in reply_list:
                            st.text(f"[{format_timestamp(msg['timestamp'])}]")
                            display_message_content(msg['content'])