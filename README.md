# 🏥 Intelligent Health Recommendation System  
### 🚀 AI-Powered Medical Triage & Hospital Recommendation Platform  

An advanced AI-driven healthcare system that bridges the gap between patients and hospitals using **voice-based input, Large Language Models (LLMs), and a real-time broker architecture**.

This system enables patients to describe symptoms in their native language and instantly connects them to the most suitable hospitals based on real-time availability, cost, and urgency.

---

## 📌 Project Overview

Accessing timely healthcare during emergencies is often difficult due to:
- Language barriers
- Lack of real-time hospital availability data
- Manual and slow communication processes

This project solves these problems by introducing a **smart AI-powered ecosystem** that:
- Converts voice symptoms into structured medical insights
- Broadcasts requests to multiple hospitals simultaneously
- Ranks hospitals dynamically based on patient priorities

---

## ❗ Problem Statement

Patients in emergency situations face:
- Difficulty explaining symptoms (especially in non-English languages)
- No visibility of which hospital has the required specialist
- Time loss in calling multiple hospitals manually

👉 **Key Issue:** *Information Asymmetry between patient needs and hospital availability*

---

## 💡 Solution Approach

We designed a **Broker-Based AI Architecture** that:
1. Accepts voice input from patients  
2. Uses AI to analyze symptoms  
3. Broadcasts requests to multiple hospitals  
4. Collects structured replies  
5. Ranks hospitals based on real-time data  

---

## 🚀 Key Features

### 👤 Patient-Side Features
- 🎤 Voice-based symptom input (multi-language support)
- 🧠 AI-powered medical analysis
- 📊 Recommended specialist detection
- 📡 One-click broadcast to multiple hospitals
- 📈 Smart hospital ranking (Urgent / Balanced / Quality)

---

### 🤖 AI & Intelligence Features
- 🗣️ Speech-to-Text (Indic language support)
- 🌐 Automatic Translation to English
- 🧠 LLM-based symptom understanding
- 📄 Structured medical output generation

---

### 🏨 Hospital-Side Features
- 📥 Dedicated hospital dashboard (Streamlit)
- 📋 Clean request summary (no raw text confusion)
- ⚡ Quick structured reply system
- 🧾 Standardized response format (wait time, cost, availability)

---

### ⚙️ System-Level Features
- 📡 Broker-based communication (fan-out architecture)
- 🔄 Real-time request-response handling
- 📊 Dynamic weighted ranking algorithm
- 🧩 Modular & scalable microservices design

---

## 🏗️ System Architecture

This system follows a **Decoupled Service-Oriented Architecture (SOA)** using a **Broker Pattern**.

### 🔹 Core Components

#### 1️⃣ Patient Application (Frontend)
- Built using Streamlit  
- Captures voice input  
- Displays AI-generated medical analysis  
- Sends requests to backend  

---

#### 2️⃣ Broker API (Backend - FastAPI)
- Acts as the **central brain**  
- Receives one request → broadcasts to all hospitals  
- Maintains separate threads for each hospital  
- Routes replies correctly  

---

#### 3️⃣ Hospital Portal (Frontend)
- Streamlit-based dashboard  
- Displays structured patient requests  
- Allows hospitals to send quick replies  

---

#### 4️⃣ AI Engine (Intelligence Layer)

**🔹 Sarvam AI**
- Speech-to-text for Indian languages  
- Translation to English  
- Handles regional dialects  

**🔹 Mistral AI (Fine-tuned)**
- Symptom analysis  
- Specialist recommendation  
- Structured medical output  

---

## 🔄 How It Works (Workflow)

1. 🎤 Patient records symptoms  
2. 🧠 AI processes & analyzes input  
3. 📡 Request sent to Broker API  
4. 🔁 Broker broadcasts to all hospitals  
5. 🏥 Hospitals respond with structured data  
6. 📊 System ranks hospitals  
7. ✅ Patient gets best recommendations  

---

## 🧮 Hospital Ranking Algorithm

The system uses a **dynamic weighted scoring model**:

\[
Score_H = \sum_{i \in F} (\hat{v_i} \cdot |w_i|)
\]

Where:
- \( v_i \) → normalized feature (distance, cost, wait time, etc.)
- \( w_i \) → weight based on patient priority

### 🎯 Ranking Modes:
- 🚨 Urgent Care → prioritize speed & distance  
- ⭐ High Quality → prioritize reviews & specialists  
- ⚖️ Balanced → mix of all factors  

---

## 🛠️ Tech Stack

| Component        | Technology |
|-----------------|-----------|
| Frontend        | Streamlit |
| Backend         | FastAPI (Python) |
| AI Models       | Mistral AI, Sarvam AI |
| Speech Processing | Sarvam STT |
| Database        | CSV (prototype) |
| Communication   | REST APIs |
| Deployment (future) | Scalable Cloud |

---

## 📂 Project Structure
