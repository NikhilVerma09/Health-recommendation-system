import requests
import os

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

def analyze_symptoms(translated_text):
    """
    Analyze medical symptoms using Mistral AI
    
    Args:
        translated_text: Translated text describing symptoms
    
    Returns:
        str: Medical analysis with elaboration, key points, and specialist recommendation
    """
    prompt = f"""
You are a medical assistant AI.

Task:
1. Elaborate what the user might be describing based on their symptoms.
2. Extract key medical points from their description.
3. Suggest the most relevant medical specialist they should consult.
4. Provide general health advice (but always recommend seeing a doctor).

Be confident, structured, and medically sound. Avoid vague statements.


User Input: "{translated_text}"

Return your response in this format:

**Symptom Analysis:**
[Provide a detailed explanation of what the symptoms might indicate]

**Key Medical Points:**
- [Point 1]
- [Point 2]

**Recommended Specialist:**
[Specific type of doctor/specialist]

**General Advice:**
[Brief health tips or immediate care suggestions]

    """

    url = "https://api.mistral.ai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        #any can be used according to accuracy and speed requirements
        # mistral-large-latest
        # mistral-small-latest
        # mistral-medium-latest
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Extract the assistant's response
        analysis = result['choices'][0]['message']['content']
        return analysis
        
    except Exception as e:
        return f"Error generating analysis: {str(e)}\n\nPlease consult a healthcare professional for medical advice."
    
