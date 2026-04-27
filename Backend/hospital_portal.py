import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# URL of our central "Broker" API
BROKER_API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide", page_title="Hospital Portal")

# --- CSS Styling ---
st.markdown("""
<style>
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .stButton>button[kind="primary"] { background-color: #007bff; color: white; border: none; }
    .stButton>button[kind="secondary"] { border: 1px solid #007bff; color: #007bff; }
    
    .analysis-request-card {
        background-color: #fff8e1;
        border: 1px solid #ffc107;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        color: #333; /* <<< THIS IS THE FIX for white text */
    }
    .analysis-request-card h3 {
        border-bottom: 2px solid #ffc107;
        padding-bottom: 5px;
        color: #ff8f00;
    }
    .analysis-request-card ul { padding-left: 20px; }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
@st.cache_data(ttl=5)
def get_hospital_list():
    try:
        r = requests.get(f"{BROKER_API_URL}/api/hospitals")
        return r.json() if r.status_code == 200 else []
    except requests.ConnectionError:
        return []

@st.cache_data(ttl=5)
def get_hospital_inbox(hospital_name):
    try:
        r = requests.get(f"{BROKER_API_URL}/api/hospital-inbox/{hospital_name}")
        return r.json() if r.status_code == 200 else []
    except:
        return []

def send_hospital_reply(thread_id, hospital_name, content_str):
    try:
        payload = {"thread_id": thread_id, "hospital_name": hospital_name, "content": content_str}
        r = requests.post(f"{BROKER_API_URL}/api/hospital-reply", json=payload)
        if r.status_code == 200:
            st.cache_data.clear()
            return True, "Reply sent!"
        else:
            return False, r.json().get("detail", "Unknown error")
    except Exception as e:
        return False, f"Failed to connect: {e}"

def format_timestamp(iso_string):
    try:
        return datetime.fromisoformat(iso_string).strftime('%Y-%m-%d %H:%M')
    except:
        return ""

# --- Login View ---
if "hospital_name" not in st.session_state:
    st.session_state.hospital_name = None

if not st.session_state.hospital_name:
    st.title("🏥 Hospital Portal Login")
    hospitals = get_hospital_list()
    if not hospitals:
        st.error("❌ **Broker API is Offline!**")
        st.code("uvicorn broker_api:app --reload --port 8000", language="bash")
    else:
        selected_hospital = st.selectbox("Select your hospital", [h["name"] for h in hospitals], index=None, placeholder="-- Select --")
        if st.button("Login") and selected_hospital:
            st.session_state.hospital_name = selected_hospital
            st.rerun()
else:
    # --- Main Portal View ---
    hospital_name = st.session_state.hospital_name
    st.sidebar.title(f"🏥 {hospital_name}")
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.hospital_name = None
        st.session_state.selected_thread = None
        st.cache_data.clear()
        st.rerun()

    st.sidebar.header("Inbox (Pending Replies)")
    if st.sidebar.button("Refresh Inbox"):
        st.cache_data.clear()
        st.session_state.selected_thread = None
        st.rerun()

    # --- Inbox (Sidebar) ---
    inbox = get_hospital_inbox(hospital_name)
    if not inbox:
        st.sidebar.info("No new messages.")
    
    if "selected_thread" not in st.session_state:
        st.session_state.selected_thread = None

    for thread in inbox:
        thread_id = thread["thread_id"]
        is_selected = (st.session_state.selected_thread and st.session_state.selected_thread["thread_id"] == thread_id)
        if st.sidebar.button(f"Thread: {thread_id[:8]}...", use_container_width=True, type="primary" if is_selected else "secondary"):
            st.session_state.selected_thread = thread
            st.rerun() # Use rerun to handle selection change

    # --- Chat View (Main Area) ---
    st.title("Conversation Viewer")
    
    if not st.session_state.selected_thread:
        st.info("Select a conversation from the inbox on the left.")
    else:
        thread = st.session_state.selected_thread
        thread_id = thread["thread_id"]
        
        st.subheader(f"Viewing Thread: {thread_id}")
        
        # --- Smart Chat Display ---
        chat_container = st.container(height=400, border=True)
        is_analysis_request = False
        specialist_name = "specialist" # Default
        
        for msg in thread["messages"]:
            with chat_container.chat_message(msg["role"]):
                st.markdown(f"*{format_timestamp(msg['timestamp'])}*")
                try:
                    data = json.loads(msg["content"])
                    if isinstance(data, dict) and data.get("type") == "SYMPTOM_ANALYSIS":
                        # This is the structured request from the user
                        is_analysis_request = True
                        analysis = data.get("data", {})
                        specialist_name = analysis.get('Recommended Specialist', 'specialist')
                        st.markdown(f"""
                        <div class="analysis-request-card">
                            <h3>Symptom Analysis Request</h3>
                            <p><strong>Recommended Specialist: {analysis.get('Recommended Specialist', 'N/A')}</strong></p>
                            <p><strong>Symptom Analysis:</strong> {analysis.get('Symptom Analysis', 'N/A')}</p>
                            <strong>Key Medical Points:</strong>
                            <ul>
                                {"".join(f"<li>{item}</li>" for item in analysis.get('Key Medical Points', []))}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(msg["content"]) # Show other JSON as text
                except (json.JSONDecodeError, TypeError):
                    st.markdown(msg["content"]) # Plain text message
        
        # --- Smart Reply Form ---
        st.markdown("---")
        st.subheader("Send Reply")
        
        if is_analysis_request:
            # Show the structured reply form
            st.info("This is a structured analysis request. Please fill out the form below.")
            with st.form(key="structured_reply_form", clear_on_submit=True):
                st.markdown(f"##### Specialist Availability")
                avail = st.radio(f"Is a '{specialist_name}' available?", ("Yes", "No", "Uncertain"), horizontal=True, index=0)
                
                st.markdown("##### Appointment Details")
                wait_time = st.number_input("Est. Wait Time (in minutes)", min_value=0, step=10, value=30)
                cost = st.text_input("Estimated Cost", placeholder="e.g., $100 - $150 or 'Covered by Insurance'")
                
                st.markdown("##### Additional Notes")
                notes = st.text_area("Notes for patient", placeholder="e.g., 'Please bring any relevant medical records.'")
                
                submit_button = st.form_submit_button("Send Structured Reply", type="primary")

                if submit_button:
                    # Package the structured reply
                    reply_data = {
                        "type": "HOSPITAL_RESPONSE",
                        "data": {
                            "specialist_available": avail,
                            "wait_time_mins": wait_time,
                            "estimated_cost": cost,
                            "notes": notes
                        }
                    }
                    reply_str = json.dumps(reply_data)
                    success, message = send_hospital_reply(thread_id, hospital_name, reply_str)
                    if success:
                        st.success(message)
                        st.session_state.selected_thread = None
                        st.rerun()
                    else:
                        st.error(message)
        else:
            # Show the plain text reply form
            st.info("This is a plain text chat.")
            with st.form(key="text_reply_form", clear_on_submit=True):
                reply_content = st.text_area("Your Reply:", height=150, placeholder="Type your reply here...")
                submit_button = st.form_submit_button("Send Reply")
                
                if submit_button:
                    if not reply_content:
                        st.error("Please enter a reply.")
                    else:
                        success, message = send_hospital_reply(thread_id, hospital_name, reply_content)
                        if success:
                            st.success(message)
                            st.session_state.selected_thread = None
                            st.rerun()
                        else:
                            st.error(message)