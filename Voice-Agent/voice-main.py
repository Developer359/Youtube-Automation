import os
import subprocess
import sys


def run_script(script_name):
  script_path = os.path.join(os.path.dirname(__file__), script_name)
  print(f"\n🚀 Executing: {script_name}...")

  # Run the script using the current python interpreter
  result = subprocess.run([sys.executable, script_path])

  if result.returncode != 0:
    raise RuntimeError(
        f"Script '{script_name}' failed with exit code {result.returncode}"
    )
  print(f"✅ Finished: {script_name}")


def run_pipeline():
  print("==================================================")
  print("🎙️ STARTING VOICE-AGENT AUTOMATION PIPELINE")
  print("==================================================")

  try:
    # 1. Run script division step
    run_script("ai-script-divide.py")

    # 2. Run voice generation & AI verification check step
    run_script("voiceover.py")

    # 3. Run audio combination step via FFmpeg
    run_script("combine-voice.py")

    print("\n==================================================")
    print("🎉 FULL PIPELINE COMPLETED SUCCESSFULLY!")
    print(
        "📁 Final Combined Audio saved to:"
        " Voice-Agent/Final-Output/final_combined.mp3"
    )
    print("==================================================")

  except Exception as e:
    print(f"\n❌ Pipeline halted due to an error: {e}")
    sys.exit(1)


if __name__ == "__main__":
  run_pipeline()