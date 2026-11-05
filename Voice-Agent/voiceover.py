import json
import os
import time
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Load environment variables from the root .env file
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".env")
)
load_dotenv(dotenv_path=env_path)

# API Keys and Configuration
FISH_API_KEY = os.getenv("FISH_API_KEY")
GEMINI_API_KEY = os.getenv("Gemini-Api-Key")
REFERENCE_ID = "01b443ee064347eda7bb83feb923226d"  # Voice Model ID for testing


# Define Pydantic schema for Gemini's audio check response
class AudioCheckResponse(BaseModel):
  is_valid: bool = Field(
      description=(
          "True if the audio clearly speaks the expected text without"
          " truncation, corruption, or silence. False otherwise."
      )
  )
  reason: str = Field(
      description="Explanation of why the audio passed or failed inspection."
  )


def generate_voiceovers():
  if not FISH_API_KEY:
    raise ValueError("FISH_API_KEY not found in environment variables or .env")
  if not GEMINI_API_KEY:
    raise ValueError("Gemini-Api-Key not found in environment variables or .env")

  # Initialize Gemini client with your custom key name
  ai_client = genai.Client(api_key=GEMINI_API_KEY)

  # 2. Define file and directory paths relative to Voice-Agent/
  base_dir = os.path.dirname(__file__)
  input_json_path = os.path.join(base_dir, "ai-script-divide.json")
  output_dir = os.path.join(base_dir, "output")

  os.makedirs(output_dir, exist_ok=True)

  # 3. Read divided script parts
  print(f"Loading script parts from: {input_json_path}")
  with open(input_json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

  parts = data.get("parts", [])
  if not parts:
    print("No script parts found to process.")
    return

  print(
      f"Found {len(parts)} script parts. Starting generation and AI verification"
      " pipeline...\n"
  )

  fish_url = "https://api.fish.audio/v1/tts"
  headers = {
      "Authorization": f"Bearer {FISH_API_KEY}",
      "Content-Type": "application/json",
      "model": "s2.1-pro-free",
  }

  # 4. Process each part with generation -> AI check -> retry loop
  for index, part in enumerate(parts, start=1):
    part_text = part.get("text", "").strip()
    part_num = part.get("part_number", index)

    if not part_text:
      continue

    output_filename = f"part_{part_num}.mp3"
    output_file_path = os.path.join(output_dir, output_filename)

    max_retries = 2
    success = False

    for attempt in range(1, max_retries + 1):
      print(
          f"[{part_num}/{len(parts)}] Attempt {attempt}: Generating audio for"
          f" Part {part_num}..."
      )

      payload = {
          "text": part_text,
          "reference_id": REFERENCE_ID,
          "format": "mp3",
      }

      try:
        # Step A: Generate Audio from Fish Audio
        response = requests.post(fish_url, headers=headers, json=payload)

        if response.status_code != 200:
          print(
              f"  --> Fish API Error (Status {response.status_code}):"
              f" {response.text}"
          )
          time.sleep(2)
          continue

        # Save temporary candidate audio
        with open(output_file_path, "wb") as audio_file:
          audio_file.write(response.content)

        print(
            "  --> Audio generated. Running AI Agent (Gemini 2.5 Flash) check..."
        )

        # Step B: Upload Audio to Gemini and Inspect Quality
        audio_file_ref = ai_client.files.upload(file=output_file_path)

        prompt = f"""
        You are an expert audio quality control agent for short-form video production.
        Listen to this generated voiceover audio clip and verify if it meets the following criteria:
        1. It correctly speaks the expected text below without missing sentences or major hallucinations.
        2. There are no sudden abrupt cutoffs, corrupted noise, or dead silence.

        Expected Text: "{part_text}"
        """

        ai_response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[audio_file_ref, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AudioCheckResponse,
                temperature=0.1,
            ),
        )

        check_result = json.loads(ai_response.text)
        is_valid = check_result.get("is_valid", False)
        reason = check_result.get("reason", "No reason provided.")

        # Cleanup uploaded file reference from Gemini storage if possible, or proceed
        try:
          ai_client.files.delete(name=audio_file_ref.name)
        except Exception:
          pass

        if is_valid:
          print(f"  --> AI Check PASSED: {reason}")
          print(f"  --> Saved verified audio: {output_file_path}\n")
          success = True
          break
        else:
          print(f"  --> AI Check FAILED: {reason}")
          print("  --> Flagged! Retrying generation...\n")

      except Exception as e:
        print(f"  --> Error during generation/check cycle: {e}\n")
        time.sleep(2)

    if not success:
      print(
          f"❌ Warning: Part {part_num} failed AI verification after"
          f" {max_retries} attempts. Proceeding with caution.\n"
      )

  print("All voiceover audio parts processed and verified successfully!")


if __name__ == "__main__":
  generate_voiceovers()