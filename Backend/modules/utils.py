import re

def parse_llm_analysis(markdown_text):
    """
    Parses the structured markdown response from the LLM into a Python dictionary.
    Handles potential parsing errors gracefully.
    """
    analysis = {}
    
    # Use regex to find content between headings
    try:
        analysis['Symptom Analysis'] = re.search(
            r'\*\*Symptom Analysis:\*\*(.*?)\*\*Key Medical Points:\*\*', 
            markdown_text, re.DOTALL | re.IGNORECASE
        ).group(1).strip()
    except Exception:
        analysis['Symptom Analysis'] = "N/A"

    try:
        key_points_raw = re.search(
            r'\*\*Key Medical Points:\*\*(.*?)\*\*Recommended Specialist:\*\*', 
            markdown_text, re.DOTALL | re.IGNORECASE
        ).group(1).strip()
        # Split points by newline and strip '- '
        analysis['Key Medical Points'] = [
            point.strip().lstrip('- ') for point in key_points_raw.split('\n') if point.strip()
        ]
    except Exception:
        analysis['Key Medical Points'] = []

    try:
        analysis['Recommended Specialist'] = re.search(
            r'\*\*Recommended Specialist:\*\*(.*?)\*\*General Advice:\*\*', 
            markdown_text, re.DOTALL | re.IGNORECASE
        ).group(1).strip()
    except Exception:
        analysis['Recommended Specialist'] = "N/A"

    try:
        # Get everything from "General Advice:" to the end
        analysis['General Advice'] = re.search(
            r'\*\*General Advice:\*\*(.*)', 
            markdown_text, re.DOTALL | re.IGNORECASE
        ).group(1).strip()
    except Exception:
        analysis['General Advice'] = "N/A"

    # Handle cases where parsing might fail
    if all(v in [None, [], "N/A"] for v in analysis.values()):
        return {
            'Symptom Analysis': 'Could not parse LLM response. Displaying raw text.',
            'Key Medical Points': [markdown_text],
            'Recommended Specialist': 'N/A',
            'General Advice': 'N/A'
        }
        
    return analysis