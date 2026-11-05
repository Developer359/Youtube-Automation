import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Load environment variables from the root directory explicitly
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".env")
)
load_dotenv(dotenv_path=env_path)

# Retrieve API key using your custom name
api_key = os.getenv("Gemini-Api-Key")


# Define the desired output structure using Pydantic
class ScriptPart(BaseModel):
  part_number: int = Field(description="Sequential part index starting at 1.")
  text: str = Field(
      description=(
          "Exact substring of the original script text for this ~15-second"
          " segment. Do NOT modify, paraphrase, or change any words."
      )
  )


class ScriptDivisionResponse(BaseModel):
  title: str
  total_parts: int
  parts: list[ScriptPart]


def divide_script():
  input_path = os.path.join(
      os.path.dirname(__file__), "..", "Agents", "ai-script.json"
  )
  output_path = os.path.join(os.path.dirname(__file__), "ai-script-divide.json")

  print(f"Reading script from: {input_path}")
  with open(input_path, "r", encoding="utf-8") as f:
    input_data = json.load(f)

  script_title = input_data.get("title", "")
  script_text = input_data.get("script_text", "")

  if not script_text:
    raise ValueError("No 'script_text' found in ai-script.json")

  if api_key:
    client = genai.Client(api_key=api_key)
  else:
    raise ValueError(
        "Gemini-Api-Key not found in environment variables or .env file."
    )

  prompt = f"""
    You are an expert audio/video script editor. 
    Split the following script text into sequential chunks where each chunk takes approximately 15 seconds to speak naturally (roughly 35 to 45 words per chunk).

    CRITICAL RULES:
    1. Do NOT change, fix, add, or remove ANY words from the original script text. Every single word must be preserved verbatim.
    2. Maintain the exact order of the script.

    Title: {script_title}
    Script Text:
    {script_text}
    """

  print("Calling Gemini model to divide the script into ~15s parts...")

  response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents=prompt,
      config=types.GenerateContentConfig(
          response_mime_type="application/json",
          response_schema=ScriptDivisionResponse,
          temperature=0.1,
      ),
  )

  result_data = json.loads(response.text)

  with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result_data, f, indent=4, ensure_ascii=False)

  print(f"Successfully saved divided script parts to: {output_path}")
  print(
      f"Total parts generated: {result_data.get('total_parts', len(result_data.get('parts', [])))}"
  )


if __name__ == "__main__":
  divide_script()