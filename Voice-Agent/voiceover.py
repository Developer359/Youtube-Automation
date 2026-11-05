import json
import os
import requests
from dotenv import load_dotenv

# 1. Load environment variables from the root .env file
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".env")
)
load_dotenv(dotenv_path=env_path)

# API Key and Reference Model configuration
FISH_API_KEY = os.getenv("FISH_API_KEY")
REFERENCE_ID = "01b443ee064347eda7bb83feb923226d"  # Voice Model ID for testing


def generate_voiceovers():
  if not FISH_API_KEY:
    raise ValueError("FISH_API_KEY not found in environment variables or .env")

  # 2. Define file and directory paths relative to Voice-Agent/
  base_dir = os.path.dirname(__file__)
  input_json_path = os.path.join(base_dir, "ai-script-divide.json")
  output_dir = os.path.join(base_dir, "output")

  # Create output directory if it doesn't exist
  os.makedirs(output_dir, exist_ok=True)

  # 3. Read the divided script parts
  print(f"Loading script parts from: {input_json_path}")
  with open(input_json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

  parts = data.get("parts", [])
  if not parts:
    print("No script parts found to process.")
    return

  print(
      f"Found {len(parts)} script parts. Starting voice generation with free"
      " model (s2.1-pro-free)...\n"
  )

  # Fish Audio REST API endpoint
  url = "https://api.fish.audio/v1/tts"
  headers = {
      "Authorization": f"Bearer {FISH_API_KEY}",
      "Content-Type": "application/json",
      "model": "s2.1-pro-free",  # <-- Added header for the free model tier
  }

  # 4. Loop through parts one by one
  for index, part in enumerate(parts, start=1):
    part_text = part.get("text", "").strip()
    part_num = part.get("part_number", index)

    if not part_text:
      continue

    print(
        f"[{part_num}/{len(parts)}] Processing Part {part_num}: '{part_text[:40]}...'"
    )

    payload = {
        "text": part_text,
        "reference_id": REFERENCE_ID,
        "format": "mp3",
    }

    try:
      # Send request to Fish Audio API using free model header
      response = requests.post(url, headers=headers, json=payload)

      if response.status_code == 200:
        output_filename = f"part_{part_num}.mp3"
        output_file_path = os.path.join(output_dir, output_filename)

        with open(output_file_path, "wb") as audio_file:
          audio_file.write(response.content)

        print(f"  --> Saved: {output_file_path}\n")
      else:
        print(
            f"  --> Failed! Status Code: {response.status_code}, Response:"
            f" {response.text}\n"
        )

    except Exception as e:
      print(f"  --> Error during API request for Part {part_num}: {e}\n")

  print("All voiceover audio parts processed successfully!")


if __name__ == "__main__":
  generate_voiceovers()