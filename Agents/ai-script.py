import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env file from the root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Retrieve API key from environment variables
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini-Api-Key")
client = genai.Client(api_key=api_key)

def generate_script():
    # Load the research topic from ai-research.json
    research_path = os.path.join(os.path.dirname(__file__), "ai-research.json")
    if not os.path.exists(research_path):
        print(f"[ERROR] {research_path} not found. Please run ai-research.py first.")
        return

    with open(research_path, "r", encoding="utf-8") as f:
        research_data = json.load(f)

    selected_topic = research_data.get("selected_topic", {})
    if not selected_topic:
        print("[ERROR] No selected_topic found in ai-research.json.")
        return

    prompt = f"""
    You are an elite YouTube short-form video scriptwriter specializing in viral "What If" and human behavior videos.
    
    Using the following research topic data:
    - Title: {selected_topic.get('title')}
    - Hook Reference: {selected_topic.get('hook')}
    - Scientific/Psychological Basis: {selected_topic.get('scientific_or_psychological_basis')}
    - Viewer Appeal: {selected_topic.get('viewer_appeal')}

    Task:
    Write a hyper-engaging, crystal clear, extremely simple English script structured by exact days or steps showing shocking results.
    
    CRITICAL WRITING RULES:
    1. SIMPLE & CLEAR: Use short, punchy, everyday conversational English. Avoid complex words, fancy vocabulary, or awkward sentence structures. Every sentence must flow naturally and instantly make sense when spoken aloud.
    2. EXACT DAY / STEP MARKERS: Use clear and precise day markers (e.g., "Day 1", "Day 10", "Day 20", "Day 30") matching the topic timeline directly with a smooth, engaging flow.
    3. CALL TO ACTION (CTA): At the very end of the script, add a quick, natural, and engaging call-to-action asking viewers to comment their thoughts and subscribe to the channel.
    4. LENGTH CONSTRAINT: Strictly under 55 seconds when spoken at a normal pace (Target total word count: between 110 and 125 words). 

    Return the response strictly as a valid JSON object with the following exact structure:
    {{
      "title": "{selected_topic.get('title')}",
      "generated_at": "",
      "estimated_duration_seconds": 45,
      "word_count": 0,
      "script_text": "Full script text here..."
    }}
    """

    print("[INFO] Generating script with CTA using Gemini 3.5 Flash-Lite...")

    response = client.models.generate_content(
        model='gemini-3.5-flash-lite',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    try:
        data = json.loads(response.text)
        data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate actual word count
        script_text = data.get("script_text", "")
        words = script_text.split()
        data["word_count"] = len(words)
        
        # Save output to ai-script.json inside the Agents folder
        output_path = os.path.join(os.path.dirname(__file__), "ai-script.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        print(f"[SUCCESS] Script successfully saved to {output_path}")
        print(json.dumps(data, indent=4))
        
    except Exception as e:
        print(f"[ERROR] Failed to parse or save JSON: {e}")
        print(response.text)

if __name__ == "__main__":
    generate_script()