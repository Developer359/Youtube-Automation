import os
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env file from the root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Retrieve API key from environment variables
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini-Api-Key")
client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"

# Word-count thresholds that decide how many prompts a sentence gets
SHORT_MAX = 18    # <= 18 words  -> 1 prompt
MEDIUM_MAX = 35   # 19-35 words  -> 2 prompts
                  # > 35 words   -> 3 prompts


def split_sentences(text):
    """Split text into sentences (supports . ! ? and Urdu/Hindi full stops)."""
    parts = re.split(r'(?<=[.!?۔।])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def prompts_needed(sentence):
    """Decide how many image prompts a sentence needs based on its length."""
    words = len(sentence.split())
    if words <= SHORT_MAX:
        return 1
    if words <= MEDIUM_MAX:
        return 2
    return 3


def get_segment_text(segment):
    """Segments may be plain strings or dicts, so handle both."""
    if isinstance(segment, str):
        return segment
    for key in ("script_segment", "text", "segment", "content", "script"):
        if key in segment:
            return segment[key]
    return ""


def generate_segment_prompts(part_number, sentences):
    """Ask Gemini for flux prompts for every sentence of one segment."""
    sentence_inputs = [
        {"id": i + 1, "sentence": s, "required_prompts": prompts_needed(s)}
        for i, s in enumerate(sentences)
    ]

    prompt = f"""
    You are an expert AI prompt engineer specializing in detailed image generation
    prompts optimized for **Flux 2 Klein 9b**.

    Task:
    For EVERY sentence below, write exactly "required_prompts" image prompts.
    - If required_prompts is 1, the single prompt covers the whole sentence.
    - If required_prompts is 2 or 3, split the sentence into that many sequential
      scenes (beginning -> middle -> end) so the visual story flows smoothly.
    - Never skip a sentence and never return more or fewer prompts than required.

    STYLE REQUIREMENTS:
    - Simple 2D stickman animation style, minimalist, expressive, clean lines,
      solid or clean background, optimized for Flux 2 Klein 9b.
    - Keep the stickman character consistent across all prompts (same look, same
      line style, same color palette).
    - Each prompt must be self-contained: describe the character, pose, emotion,
      props, setting, and camera framing. No text, captions, or watermarks in the image.

    Input sentences:
    {json.dumps(sentence_inputs, indent=2, ensure_ascii=False)}

    Return strictly valid JSON in this exact structure:
    {{
      "sentences": [
        {{
          "id": 1,
          "flux_prompts": ["prompt for scene 1", "prompt for scene 2"]
        }}
      ]
    }}
    """

    print(f"[INFO] Part {part_number}: generating prompts for {len(sentences)} sentences...")

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            data = json.loads(response.text)
            return {item["id"]: item["flux_prompts"] for item in data["sentences"]}
        except Exception as e:
            print(f"[WARN] Part {part_number} attempt {attempt + 1} failed: {e}")
    return {}


def generate_prompts():
    # Load divided script from ai-script-divide.json
    divide_path = os.path.join(os.path.dirname(__file__), '..', "ai-script-divide.json")
    if not os.path.exists(divide_path):
        print(f"[ERROR] {divide_path} not found. Please run ai-script-divide.py first.")
        return

    with open(divide_path, "r", encoding="utf-8") as f:
        divide_data = json.load(f)

    segments = divide_data.get("segments", [])
    if not segments:
        print("[ERROR] No segments found in ai-script-divide.json.")
        return

    prompt_segments = []
    prompt_counter = 1  # global numbering across all parts

    for part_number, segment in enumerate(segments, start=1):
        segment_text = get_segment_text(segment)
        sentences = split_sentences(segment_text)
        if not sentences:
            print(f"[WARN] Part {part_number} has no sentences, skipping.")
            continue

        result = generate_segment_prompts(part_number, sentences)

        sentence_prompts = []
        for i, sentence in enumerate(sentences, start=1):
            needed = prompts_needed(sentence)
            flux_prompts = result.get(i, [])

            if len(flux_prompts) != needed:
                print(f"[WARN] Part {part_number}, sentence {i}: expected {needed} "
                      f"prompts, got {len(flux_prompts)}.")
            if not flux_prompts:
                continue

            for scene_index, flux_prompt in enumerate(flux_prompts, start=1):
                sentence_prompts.append({
                    "prompt_number": prompt_counter,
                    "sentence_number": i,
                    "scene_in_sentence": scene_index,
                    "total_scenes_in_sentence": len(flux_prompts),
                    "source_sentence": sentence,
                    "flux_prompt": flux_prompt,
                })
                prompt_counter += 1

        prompt_segments.append({
            "part": part_number,
            "script_segment": segment_text,
            "sentence_prompts": sentence_prompts,
        })

    output = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_prompts": prompt_counter - 1,
        "prompt_segments": prompt_segments,
    }

    output_path = os.path.join(os.path.dirname(__file__), "prompt-agent.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"[SUCCESS] {output['total_prompts']} prompts saved to {output_path}")


if __name__ == "__main__":
    generate_prompts()