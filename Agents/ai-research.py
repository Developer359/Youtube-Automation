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

# Initialize the Gemini client with the explicit key
client = genai.Client(api_key=api_key)

def research_trending_topic():
    prompt = """
    You are an elite YouTube content strategist and researcher specializing in the "What If", human behavior, human relationships, and human health niche (e.g., physiological extremes, psychological experiments, lifestyle shifts).
    
    Step 1: Brainstorm 3 distinct, highly compelling potential video topics within this niche.
    Step 2: Evaluate and compare them for maximum viral potential, high Click-Through Rate (CTR), and audience engagement specifically tailored for viewers in the US, UK, and Australia.
    Step 3: Select the single best, most trending, and highest-potential topic among the three.
    
    Return the response strictly as a valid JSON object containing ONLY that selected top topic in the following exact structure:
    {
      "niche": "Human Behavior, Health & Relationships / What If",
      "generated_at": "",
      "target_markets": ["US", "UK", "AUS"],
      "selected_topic": {
        "title": "High-CTR YouTube Video Title",
        "hook": "The gripping 5-second opening hook to maximize audience retention",
        "scientific_or_psychological_basis": "The core fact, study, or psychological trigger behind the topic",
        "viewer_appeal": "Why this topic triggers high curiosity and clicks for US/UK/AUS audiences"
      }
    }
    """

    print("[INFO] Generating options and selecting the top trending topic for US, UK, AUS using Gemini 3.5 Flash-Lite...")
    
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
        
        # Save output to ai-research.json inside the Agents folder
        output_path = os.path.join(os.path.dirname(__file__), "ai-research.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        print(f"[SUCCESS] Selected topic successfully saved to {output_path}")
        print(json.dumps(data, indent=4))
        
    except Exception as e:
        print(f"[ERROR] Failed to parse or save JSON: {e}")
        print(response.text)

if __name__ == "__main__":
    research_trending_topic()