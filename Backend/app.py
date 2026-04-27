import streamlit as st
import pyaudio
import wave
import threading
import tempfile
import time
import requests
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd 
import re 


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)


backend_path = os.path.join(os.path.dirname(__file__), 'Backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)


from modules.speech_to_text import transcribe_audio
from modules.translate import translate_to_english
from modules.llm_analysis import analyze_symptoms
from modules.utils import parse_llm_analysis

# --- App Config ---
st.set_page_config(page_title="AI Medical Assistant", layout="wide")
BROKER_API_URL = "http://127.0.0.1:8000"

# --- CSS Styling ---
def load_css():
    st.markdown("""
    <style>
        /* General */
        .stButton>button {
            border-radius: 8px;
            padding: 10px 16px;
            font-weight: 600;
        }
        .stButton>button[kind="primary"] {
            background-color: #007bff;
            color: white;
            border: none;
        }
        .stButton>button[kind="primary"]:hover {
            background-color: #0056b3;
        }
        .stButton>button[kind="secondary"] {
            border: 1px solid #007bff;
            color: #007bff;
        }
        .stButton>button[kind="secondary"]:hover {
            background-color: #f0f7ff;
        }
        
        /* Analysis Card */
        .analysis-card {
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .analysis-card h3 {
            border-bottom: 2px solid #007bff;
            padding-bottom: 5px;
            color: #007bff;
        }
        .analysis-card ul {
            padding-left: 20px;
        }
        
        /* Hospital Reply Card */
        .reply-card {
            background-color: #f0fff4;
            border: 1px solid #1a936f;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            color: #333; /* Fix for dark mode */
        }
        .reply-card-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #116c52;
            border-bottom: 1px solid #a3e0c9;
            padding-bottom: 5px;
            margin-bottom: 10px;
        }
        .reply-card-item {
            margin-bottom: 5px;
        }
        .reply-card-item strong {
            color: #333;
        }
        
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- Helper Functions (for Chat) ---
@st.cache_data(ttl=1)
def get_hospital_list():
    try:
        r = requests.get(f"{BROKER_API_URL}/api/hospitals")
        return r.json() if r.status_code == 200 else []
    except requests.ConnectionError:
        return []

def fetch_chat_history(thread_id):
    try:
        r = requests.get(f"{BROKER_API_URL}/api/chat-history/{thread_id}")
        return r.json()["messages"] if r.status_code == 200 else []
    except:
        return [{"role": "system", "content": "Error fetching history.", "timestamp": ""}]

def fetch_broadcast_replies(broadcast_id):
    try:
        r = requests.get(f"{BROKER_API_URL}/api/broadcast-replies/{broadcast_id}")
        return r.json() if r.status_code == 200 else {}
    except:
        return {"error": "Could not connect to broker."}

def format_timestamp(iso_string):
    try:
        return datetime.fromisoformat(iso_string).strftime('%Y-%m-%d %H:%M')
    except:
        return ""

def display_message_content(content_string):
    """Smartly displays message content as JSON card or plain text."""
    try:
        data = json.loads(content_string)
        if isinstance(data, dict) and "type" in data:
            if data["type"] == "HOSPITAL_RESPONSE" and "data" in data:
                resp = data["data"]
                st.markdown(f"""
                <div class.reply-card>
                    <div class.reply-card-header">Hospital Response</div>
                    <div class.reply-card-item"><strong>Specialist Available:</strong> {resp.get('specialist_available', 'N/A')}</div>
                    <div class.reply-card-item"><strong>Est. Wait Time:</strong> {resp.get('wait_time_mins', 'N/A')} minutes</div>
                    <div class.reply-card-item"><strong>Est. Cost:</strong> {resp.get('estimated_cost', 'N/A')}</div>
                    <div class.reply-card-item"><strong>Notes:</strong> {resp.get('notes', 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)
            elif data["type"] == "SYMPTOM_ANALYSIS" and "data" in data:
                parsed = data["data"]
                st.markdown(f"""
                <div class.analysis-card">
                    <h3>Symptom Analysis (Sent)</h3>
                    <p><strong>Recommended Specialist: {parsed.get('Recommended Specialist', 'N/A')}</strong></p>
                    <p>{parsed.get('Symptom Analysis', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.json(data)
        else:
            st.json(data)
    except (json.JSONDecodeError, TypeError):
        st.markdown(content_string)

# --- Recording Logic (from app.py) ---
def record_audio(file_path, event):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        frames = []
        while event.is_set():
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
    except Exception as e:
        st.error(f"Recording error: {e}")
        if 'stream' in locals() and stream.is_active(): stream.close()
        if 'p' in locals(): p.terminate()


def convert_cost_to_score(cost_string):
    """Converts a cost string (e.g., '$100-150', 'Covered') to a 1-10 score."""
    if not cost_string or "covered" in cost_string.lower():
        return 0 # Best score
    
    # Find numbers in the string
    numbers = [int(s) for s in re.findall(r'\d+', cost_string)]
    if not numbers:
        return 5 # Neutral score if unparseable
    
    avg_cost = sum(numbers) / len(numbers)
    
    # Simple scaling: 0-50 = 2, 51-100 = 4, 101-200 = 6, 201-300 = 8, 300+ = 10
    if avg_cost <= 50: return 2
    if avg_cost <= 100: return 4
    if avg_cost <= 200: return 6
    if avg_cost <= 300: return 8
    return 10 # Worst score

# --- NEW: Ranking Logic (Copied from app2.py and MODIFIED) ---
def get_hospital_data():
    """Loads static hospital data from a CSV file."""
    try:
        return pd.read_csv('hospital_data.csv')
    except FileNotFoundError:
        st.error("`hospital_data.csv` not found.")
        return pd.DataFrame(columns=['hospital_name', 'distance', 'reviews'])

def rank_hospitals(df, situation):
    """
    Ranks hospitals based on a weighted score.
    MODIFIED to use live data for wait time, specialist, and cost.
    """
    
    # --- 1. Pre-process live data to create rankable scores ---
    
    # Map specialist availability to a 0-1 score
    df['specialist_score'] = df['specialist_available'].map({'Yes': 1.0, 'Uncertain': 0.5, 'No': 0.0}).fillna(0.0)
    
    # Rename live wait time to match ranker's expected column
    df['waiting_time'] = df['live_wait_time']
    
    # Convert cost string to a 1-10 score
    df['expense_score'] = df['live_cost'].apply(convert_cost_to_score)
    
    # Use static 'doctor_availability' as a fallback if specialist is uncertain
    # If 'Yes' or 'No', specialist_score is dominant (1.0 or 0.0)
    # If 'Uncertain' (0.5), we average with the static score
    df['doctor_availability'] = df.apply(
        lambda row: (row['specialist_score'] + (row['doctor_availability'] / 10)) / 2 if row['specialist_score'] == 0.5 else row['specialist_score'],
        axis=1
    )
    # After this, we drop specialist_score and just use doctor_availability
    
    # Define weights. We now use the 'live' data, so weights are adjusted.
    weights = {
        'Urgent Care': {
            'distance': -0.4,
            'waiting_time': -0.4, # More important now
            'doctor_availability': 0.2, # (based on specialist)
            'reviews': 0.0,
            'expense_score': 0.0
        },
        'High-Quality Focus': {
            'reviews': 0.4,
            'doctor_availability': 0.4, # (based on specialist)
            'waiting_time': -0.1,
            'distance': -0.05,
            'expense_score': -0.05 # Lower score is better
        },
        'Balanced Approach': {
            'reviews': 0.2,
            'distance': -0.2,
            'expense_score': -0.2,
            'doctor_availability': 0.2,
            'waiting_time': -0.2
        }
    }

    current_weights = weights[situation]
    normalized_df = df.copy()

    # --- 2. Normalization (from app2.py) ---
    for col in ['distance', 'waiting_time', 'doctor_availability', 'reviews', 'expense_score']:
        if col not in current_weights or current_weights[col] == 0:
            continue
            
        weight = current_weights[col]
        min_val = df[col].min()
        max_val = df[col].max()
        
        if (max_val - min_val) == 0:
            normalized_df[col] = 0.5 
            continue

        if weight < 0: # lower is better
            normalized_df[col] = (max_val - df[col]) / (max_val - min_val)
        else: # higher is better
            normalized_df[col] = (df[col] - min_val) / (max_val - min_val)

    # --- 3. Scoring (from app2.py) ---
    df['score'] = (
        normalized_df['distance'] * abs(current_weights.get('distance', 0)) +
        normalized_df['waiting_time'] * abs(current_weights.get('waiting_time', 0)) +
        normalized_df['doctor_availability'] * abs(current_weights.get('doctor_availability', 0)) +
        normalized_df['reviews'] * abs(current_weights.get('reviews', 0)) +
        normalized_df['expense_score'] * abs(current_weights.get('expense_score', 0))
    )

    return df.sort_values(by='score', ascending=False).reset_index(drop=True)

# --- Initialize Session State ---
state_keys = {
    "audio_file": None,
    "recording": False,
    "recording_thread": None,
    "recording_event": threading.Event(),
    "analysis_complete": False,
    "parsed_analysis": None,
    "raw_analysis": None,
    "broadcast_id": None
}
for key, default in state_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default
if "recording_event" not in st.session_state or st.session_state.recording_event is None:
    st.session_state.recording_event = threading.Event()


# --- Main App ---
st.title("🩺 AI Medical Assistant & Hospital Connect")
st.write("Record your symptoms, get an AI analysis, and instantly contact nearby hospitals.")

tab1, tab2 = st.tabs(["Symptom Analysis", "Hospital Chat"])

# --- TAB 1: Symptom Analysis (Unchanged) ---
with tab1:
    
    st.header("Step 1: Record Your Symptoms")
    
    col1, col2 = st.columns(2)
    if col1.button("🎤 Start Recording", disabled=st.session_state.recording):
        st.session_state.recording = True
        st.session_state.recording_event.set()
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        st.session_state.audio_file = temp_wav.name
        temp_wav.close()
        st.session_state.recording_thread = threading.Thread(
            target=record_audio, 
            args=(st.session_state.audio_file, st.session_state.recording_event), 
            daemon=True
        )
        st.session_state.recording_thread.start()
        st.info("🎙️ Recording started... Click 'Stop' when finished.")
        st.rerun()

    if col2.button("⏹️ Stop Recording", disabled=not st.session_state.recording):
        st.session_state.recording_event.clear()
        st.session_state.recording = False
        if st.session_state.recording_thread:
            st.session_state.recording_thread.join(timeout=2)
        time.sleep(0.5)
        st.success("✅ Recording stopped!")
        st.rerun()

    if st.session_state.audio_file and not st.session_state.recording:
        try:
            with open(st.session_state.audio_file, 'rb') as f:
                st.audio(f.read(), format="audio/wav")
        except Exception as e:
            st.error(f"Could not load audio: {e}")

        if st.button("🩺 Analyze Symptoms", key="process_audio"):
            try:
                if os.path.getsize(st.session_state.audio_file) > 0:
                    with st.spinner("Transcribing audio..."):
                        transcript, lang = transcribe_audio(st.session_state.audio_file)
                    st.info(f"Detected language: {lang}")
                    
                    with st.spinner("Translating to English..."):
                        english_text = translate_to_english(transcript, source_lang=lang)
                    
                    with st.spinner("Analyzing symptoms..."):
                        analysis = analyze_symptoms(english_text)
                    
                    st.session_state.analysis_complete = True
                    st.session_state.raw_analysis = analysis 
                    st.session_state.parsed_analysis = parse_llm_analysis(analysis) 
                    st.rerun()
                else:
                    st.error("Audio file is empty.")
            except Exception as e:
                st.error(f"Error during processing: {e}")
                import traceback
                st.error(traceback.format_exc())

    if st.session_state.analysis_complete:
        st.markdown("---")
        st.header("Step 2: Review Your Analysis")
        
        with st.container(border=True):
            st.markdown(st.session_state.raw_analysis, unsafe_allow_html=True)
        
        st.markdown("---")
        st.header("Step 3: Contact Hospitals")
        
        parsed = st.session_state.parsed_analysis
        specialist = parsed.get('Recommended Specialist', 'specialist')
        st.write(f"Click the button below to send this analysis to all connected hospitals to ask for appointments with a **{specialist}**.")

        if st.button("📡 Broadcast Analysis to All Hospitals", type="primary"):
            try:
                broadcast_payload = { "type": "SYMPTOM_ANALYSIS", "data": st.session_state.parsed_analysis }
                payload_str = json.dumps(broadcast_payload)
                r = requests.post(f"{BROKER_API_URL}/api/broadcast", json={"message": payload_str})
                
                if r.status_code == 200:
                    st.session_state.broadcast_id = r.json().get("broadcast_id")
                    st.success(f"Broadcast sent! Your ID is: {st.session_state.broadcast_id}")
                    st.info("Hospitals will now review your request. Go to the 'Hospital Chat' tab to see their replies.")
                    st.balloons()
                else:
                    st.error(f"Error from broker: {r.json().get('detail')}")
            except Exception as e:
                st.error(f"Failed to connect to broker: {e}")

    if st.session_state.audio_file and st.button("🔄 Reset / New Recording"):
        for key in state_keys:
            if key == "recording_event": st.session_state[key].clear()
            else: st.session_state[key] = default
        st.session_state.recording_event = threading.Event()
        st.rerun()


# --- TAB 2: Hospital Chat ---
with tab2:
    st.header("Hospital Communication Center")
    hospitals = get_hospital_list()
    if not hospitals:
        st.error("❌ **Broker API is Offline!**")
        st.markdown("Run `uvicorn broker_api:app --reload --port 8000`")
        st.stop()

    chat_tab1, chat_tab2 = st.tabs(["💬 Specific Chat", "📡 Broadcast Replies"])

   
    with chat_tab1:
        st.subheader("Chat 1-on-1 with a specific hospital")
        hospital_name = st.selectbox("Select Hospital", [h["name"] for h in hospitals], index=None, placeholder="-- Select a hospital --")
        
        if hospital_name:
            thread_key = f"chat_thread_id_{hospital_name}"
            if thread_key not in st.session_state:
                st.session_state[thread_key] = None
            thread_id = st.session_state[thread_key]

            chat_container = st.container(height=400, border=True)
            if thread_id:
                messages = fetch_chat_history(thread_id)
                for msg in messages:
                    with chat_container.chat_message(msg["role"]):
                        st.markdown(f"*{format_timestamp(msg['timestamp'])}*")
                        display_message_content(msg["content"])

            if prompt := st.chat_input("What is your question?"):
                try:
                    payload = {"hospital_name": hospital_name, "thread_id": thread_id, "message": prompt}
                    r = requests.post(f"{BROKER_API_URL}/api/chat", json=payload)
                    if r.status_code == 200:
                        if not thread_id:
                            st.session_state[thread_key] = r.json().get("thread_id")
                        st.rerun()
                    else:
                        st.error(f"Error: {r.json().get('detail')}")
                except Exception as e:
                    st.error(f"Failed to connect: {e}")
        else:
            st.info("Select a hospital to begin a 1-on-1 chat.")

   
    with chat_tab2:
        st.subheader("Ranked Hospital Replies")
        
        if not st.session_state.broadcast_id:
            st.info("You have not sent any broadcasts in this session. Send one from the 'Symptom Analysis' tab.")
        else:
            st.write(f"Showing results for Broadcast ID: `{st.session_state.broadcast_id}`")
          
            situation = st.selectbox(
                'What is your primary concern?',
                ('Urgent Care', 'High-Quality Focus', 'Balanced Approach'),
                index=2, # D
                help="Select your priority to re-rank the hospital responses."
            )
            
            if st.button("Refresh & Rank Replies"):
                # 1. Fetch live replies from broker
                replies = fetch_broadcast_replies(st.session_state.broadcast_id)
                
                if not replies:
                    st.info("No hospital replies received yet.")
                else:
                    # 2. Load static data from CSV
                    static_df = get_hospital_data()
                    
                    # 3. Process live replies into a list
                    live_data_list = []
                    for hospital_name, message_list in replies.items():
                        if not message_list: continue
                        last_msg = message_list[-1] # Get the latest reply
                        try:
                            data = json.loads(last_msg['content'])
                            if data.get("type") == "HOSPITAL_RESPONSE":
                                resp_data = data.get("data", {})
                                live_data_list.append({
                                    "hospital_name": hospital_name,
                                    "live_wait_time": resp_data.get('wait_time_mins', 999), # Default to high wait time
                                    "live_cost": resp_data.get('estimated_cost', ""),
                                    "specialist_available": resp_data.get('specialist_available', 'Uncertain'),
                                    "notes": resp_data.get('notes', 'No notes.')
                                })
                        except:
                            continue # Ignore plain text messages
                    
                    if not live_data_list:
                        st.warning("Found replies, but none were in the correct format.")
                        st.stop()
                        
                    live_df = pd.DataFrame(live_data_list)
                    
                    # 4. Merge static and live data
                    # This ensures we only rank hospitals that have BOTH replied AND are in our static CSV
                    merged_df = pd.merge(static_df, live_df, on="hospital_name", how="inner")

                    if merged_df.empty:
                        st.error("No replies from known hospitals. Check `hospital_data.csv` for name mismatches.")
                        st.stop()

                    # 5. Rank the merged data
                    ranked_df = rank_hospitals(merged_df, situation)
                    
                    st.success(f"Ranked {len(ranked_df)} replying hospitals for: `{situation}`")

                    # 6. Display ranked results (using app2.py's display logic)
                    for index, row in ranked_df.iterrows():
                        rank = index + 1
                        emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**#{rank}**"
                        
                        with st.container(border=True):
                            col1, col2 = st.columns([1, 4])
                            
                            with col1:
                                st.markdown(f"<div style='font-size: 2.5em; text-align: center; margin-top: 20px;'>{emoji}</div>", unsafe_allow_html=True)

                            with col2:
                                st.subheader(f"{row['hospital_name']}")
                                
                                # Show the live notes from the hospital
                                if row['notes']:
                                    st.info(f"**Note from hospital:** {row['notes']}")
                                
                                c1, c2, c3, c4 = st.columns(4)
                                
                                c1.metric("Specialist?", f"{row['specialist_available']}")
                                c2.metric("Est. Wait", f"{row['live_wait_time']} min")
                                c3.metric("Static Reviews", f"{row['reviews']} ⭐")
                                c4.metric("Est. Cost", f"{row['live_cost'] if row['live_cost'] else 'N/A'}")