import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uuid
import datetime
from typing import List, Dict, Optional, Any

# --- In-Memory Database ---
CHAT_THREADS: Dict[str, Dict] = {} 

# --- Helper function to load hospitals ---
def load_hospitals():
    try:
        df = pd.read_csv("hospital_data.csv")
        return [{"name": name} for name in df["hospital_name"].tolist()]
    except FileNotFoundError:
        print("FATAL ERROR: hospital_data.csv not found.")
        return []
    except KeyError:
        print("FATAL ERROR: 'hospital_name' column not found in hospital_data.csv.")
        return []

HOSPITAL_LIST = load_hospitals()
HOSPITAL_NAMES = {h["name"] for h in HOSPITAL_LIST}

# --- Pydantic Models (Data Validation) ---
class ChatMessageIn(BaseModel):
    hospital_name: str
    thread_id: Optional[str] = None
    message: str

class BroadcastMessageIn(BaseModel):
    message: str

class HospitalReplyIn(BaseModel):
    thread_id: str
    hospital_name: str
    content: str # This can be any string

class Message(BaseModel):
    role: str
    content: str
    timestamp: str

# --- FastAPI App Initialization ---
app = FastAPI(title="Hospital Chat Broker API")

# --- CORS Middleware (CRITICAL) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- API Endpoints ---

@app.on_event("startup")
async def startup_event():
    if not HOSPITAL_LIST:
        print("="*50)
        print("ERROR: No hospitals loaded. API is running but will fail.")
        print("Make sure 'hospital_data.csv' exists and has a 'hospital_name' column.")
        print("="*50)
    else:
        print(f"Broker API started. Loaded {len(HOSPITAL_LIST)} hospitals.")

@app.get("/")
def read_root():
    return {"message": "Broker API is running. Ready to connect apps."}

@app.get("/api/hospitals")
def get_hospitals():
    """Returns the list of all configured hospitals."""
    return HOSPITAL_LIST

# --- Endpoints for User App (app3.py) ---

@app.post("/api/chat")
def post_chat_message(data: ChatMessageIn):
    """Handles a specific, 1-to-1 chat message from a user."""
    if data.hospital_name not in HOSPITAL_NAMES:
        raise HTTPException(status_code=404, detail="Hospital not found")

    timestamp = datetime.datetime.now().isoformat()
    new_message = {
        "role": "user", 
        "content": data.message, 
        "timestamp": timestamp,
        "hospital_name": data.hospital_name
    }

    if data.thread_id and data.thread_id in CHAT_THREADS:
        thread_id = data.thread_id
        CHAT_THREADS[thread_id]["messages"].append(new_message)
    else:
        thread_id = f"thread-{uuid.uuid4()}"
        CHAT_THREADS[thread_id] = {
            "thread_id": thread_id,
            "broadcast_id": None,
            "hospitals_involved": [data.hospital_name],
            "messages": [new_message]
        }
    
    return {"status": "success", "thread_id": thread_id}


@app.post("/api/broadcast")
def post_broadcast_message(data: BroadcastMessageIn):
    """
    Handles a 1-to-many broadcast.
    This now creates a SEPARATE thread for EACH hospital.
    """
    broadcast_id = f"broadcast-{uuid.uuid4()}"
    timestamp = datetime.datetime.now().isoformat()
    base_message = {
        "role": "user", 
        "content": data.message, 
        "timestamp": timestamp,
        "hospital_name": "all" 
    }
    
    created_thread_ids = []
    for hospital_name in HOSPITAL_NAMES:
        thread_id = f"thread-{uuid.uuid4()}"
        CHAT_THREADS[thread_id] = {
            "thread_id": thread_id,
            "broadcast_id": broadcast_id, 
            "hospitals_involved": [hospital_name], 
            "messages": [base_message] 
        }
        created_thread_ids.append(thread_id)
    
    print(f"Broadcast {broadcast_id} fanned out to {len(created_thread_ids)} threads.")
    return {"status": "success", "broadcast_id": broadcast_id}


@app.get("/api/chat-history/{thread_id}")
def get_chat_history(thread_id: str):
    """Gets all messages for a specific chat thread."""
    if thread_id not in CHAT_THREADS:
        raise HTTPException(status_code=404, detail="Thread not found")
    return CHAT_THREADS[thread_id]


# --- !!! NEW BROADCAST REPLY LOGIC !!! ---
@app.get("/api/broadcast-replies/{broadcast_id}")
def get_broadcast_replies(broadcast_id: str):
    """
    Finds ALL threads associated with a broadcast and gathers replies.
    """
    replies = {}
    # Search all threads in the database
    for thread in CHAT_THREADS.values():
        # If a thread is tagged with this broadcast_id
        if thread["broadcast_id"] == broadcast_id:
            # Check its messages for hospital replies
            for msg in thread["messages"]:
                if msg["role"] == "hospital":
                    hospital = msg["hospital_name"]
                    if hospital not in replies:
                        replies[hospital] = []
                    replies[hospital].append(msg)
    return replies

# --- Endpoints for Hospital Portal (hospital_portal.py) ---

@app.get("/api/hospital-inbox/{hospital_name}")
def get_hospital_inbox(hospital_name: str):
    """
    Gets all threads for a hospital that are waiting for a reply.
    (This logic is now correct because each thread is separate)
    """
    if hospital_name not in HOSPITAL_NAMES:
        raise HTTPException(status_code=404, detail="Hospital not found")

    pending_threads = []
    for thread_id, thread in CHAT_THREADS.items():
        # Check if hospital is involved AND last message was from user
        if hospital_name in thread["hospitals_involved"] and thread["messages"]:
            if thread["messages"][-1]["role"] == "user":
                pending_threads.append(thread)
                
    return pending_threads

@app.post("/api/hospital-reply")
def post_hospital_reply(data: HospitalReplyIn):
    """
    Handles a reply sent from the hospital portal.
    (This logic does not need to change)
    """
    if data.thread_id not in CHAT_THREADS:
        raise HTTPException(status_code=404, detail="Thread not found")
    if data.hospital_name not in HOSPITAL_NAMES:
        raise HTTPException(status_code=404, detail="Hospital not found")  
    thread = CHAT_THREADS[data.thread_id]
    if data.hospital_name not in thread["hospitals_involved"]:
        raise HTTPException(status_code=403, detail="Hospital not authorized for this thread")

    timestamp = datetime.datetime.now().isoformat()
    new_message = {
        "role": "hospital",
        "content": data.content,
        "timestamp": timestamp,
        "hospital_name": data.hospital_name
    } 
    thread["messages"].append(new_message)
    return {"status": "reply sent"}

# --- Main execution ---
if __name__ == "__main__":
    if not HOSPITAL_LIST:
        print("Failed to start API. 'hospital_data.csv' missing or invalid.")
    else:
        print(f"Starting FastAPI Broker API on http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)

