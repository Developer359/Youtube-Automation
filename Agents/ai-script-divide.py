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

def divide_script():
    # Load the script from ai-script.json
    script_path = os.path.join(os.path.dirname(__file__), "ai-script.json")
    if not os.path.exists(script_path):
        print(f"[ERROR] {script_path} not found. Please run ai-script.py first.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    full_script = script_data.get("script_text", "")
    if not full_script:
        print("[ERROR] No script_text found in ai-script.json.")
        return

    prompt = f"""
    You are a precise text-processing assistant.
    Take the following YouTube short script and split it sentence-by-sentence into exactly TWO equal parts (Part 1 and Part 2) so that the sentence count and length are divided as evenly as possible between them. Do NOT rewrite or change any words from the script.
    For each part.

    Full Script:
    "{full_script}"

    Return the response strictly as a valid JSON object with the following exact structure:
    {{
      "generated_at": "",
      "segments": [
        {{
          "part": 1,
          "script_segment": "First half of sentences here...",
        }},
        {{
          "part": 2,
          "script_segment": "Second half of sentences here...",
        }}
      ]
    }}
    """

    print("[INFO] Splitting script sentence-wise and generating visual prompts using Gemini 3.5 Flash-Lite...")

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
        
        # Save output to ai-script-divide.json inside the Agents folder
        output_path = os.path.join(os.path.dirname(__file__), "ai-script-divide.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        print(f"[SUCCESS] Evenly divided script successfully saved to {output_path}")
        print(json.dumps(data, indent=4))
        
    except Exception as e:
        print(f"[ERROR] Failed to parse or save JSON: {e}")
        print(response.text)

if __name__ == "__main__":
    divide_script()