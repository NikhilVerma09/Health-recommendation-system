🏥 AI Medical Assistant & Hospital Broker

This project is an advanced, multi-part application designed to simulate a real-time medical triage and communication system. It connects a patient-facing application with multiple hospital portals through a central backend broker.

The system uses a suite of open-source language models, fine-tuned on medical and hospital datasets, to analyze a patient's voice symptoms in any language and instantly broadcast their needs to a network of hospitals.

🚀 Features

🎤 Voice-to-Analysis: Record symptoms in any language.

🧠 AI Triage: Uses fine-tuned models for transcription, translation, and structured symptom analysis (including a recommended specialist).

📡 Instant Broadcast: Send the AI-generated analysis to all connected hospitals simultaneously.

🏨 Hospital Portal: A dedicated, secure Streamlit app for hospital staff to receive and reply to patient requests.

📊 Live Ranking: The patient receives a ranked list of hospital replies based on live data (wait time, cost, specialist availability) and their chosen priority (e.g., Urgent, High-Quality).

🏗️ How it Works (Architecture)

This project runs as three separate applications that communicate via a central API:

1. app.py (The Patient Frontend)

This is the main Streamlit app for the patient.

Handles voice recording and file handling.

Calls the AI modules from the Backend/modules/ folder to get an analysis.

Displays the final analysis (e.g., "Recommended Specialist: Neurologist").

Sends the analysis as a "broadcast" request to the Broker.

Fetches all hospital replies from the Broker and ranks them using the logic from app2.py.

2. broker_api.py (The Backend Broker)

This is a FastAPI server that acts as the central "brain" or message queue.

Receives a single broadcast request from app.py.

"Fans out" the request by creating a separate, private chat thread for every hospital listed in hospital_data.csv.

Receives structured replies from the hospitals.

Serves the correct inbox to each hospital and the complete list of replies to the patient.

3. hospital_portal.py (The Hospital Frontend)

This is a separate Streamlit app for hospital staff.

Provides a simple "login" by selecting the hospital name.

Fetches only its own pending messages from the Broker.

Displays the patient's analysis in a clean "request card."

Provides a structured form (e.g., "Specialist Available: Yes/No", "Est. Wait Time") for a fast, formatted reply.

🗂️ File Roles

app.py: Main application for patients.

broker_api.py: FastAPI backend that routes all messages.

hospital_portal.py: Main application for hospital staff.

Backend/modules/: The "AI Engine." Connects to open-source models fine-tuned on hospital datasets for:

speech_to_text.py (Transcription)

translate.py (Translation)

llm_analysis.py (Symptom Analysis)

utils.py (Parses the AI's response)

hospital_data.csv: A static database providing the master list of hospitals and base data (distance, static reviews) for ranking.

.env: Stores the API keys for the AI models.

app2.py / app3.py: Legacy/testing files. All of their logic has been integrated into app.py.

⚡ How to Run

This system requires running three separate servers in three separate terminals.

Step 1: Install Dependencies

Make sure your venv is activated.
pip install streamlit fastapi "uvicorn[standard]" pandas requests pyaudio python-dotenv



Step 2: Run the Servers

1. Terminal 1 (Run the Broker)

This is the central "brain." It must be running first.
uvicorn broker_api:app --reload --port 8000


2. Terminal 2 (Run the Patient App)

streamlit run app.py
(This will open in your browser at http://localhost:8501)

3. Terminal 3 (Run the Hospital Portal)

streamlit run hospital_portal.py
(This will open in a new tab at http://localhost:8502)