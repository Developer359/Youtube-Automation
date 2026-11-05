import os
import subprocess


def combine_audio_parts():
  base_dir = os.path.dirname(__file__)
  output_dir = os.path.join(base_dir, "output")
  final_output_dir = os.path.join(base_dir, "Final-Output")

  # Create Final-Output directory if it doesn't exist
  os.makedirs(final_output_dir, exist_ok=True)

  if not os.path.exists(output_dir):
    print(f"Error: Output directory not found at {output_dir}")
    return

  # 1. Gather and sort part files numerically (e.g. part_1.mp3, part_2.mp3...)
  files = os.listdir(output_dir)
  part_files = [f for f in files if f.startswith("part_") and f.endswith(".mp3")]

  try:
    part_files.sort(
        key=lambda x: int(x.replace("part_", "").replace(".mp3", ""))
    )
  except Exception:
    part_files.sort()  # Fallback to standard sorting if naming varies

  if not part_files:
    print("No audio part files found to combine in output/ folder.")
    return

  print(f"Found {len(part_files)} parts to combine: {part_files}")

  # 2. Create a temporary text file listing the parts for FFmpeg's concat demuxer
  list_file_path = os.path.join(base_dir, "file_list.txt")
  with open(list_file_path, "w", encoding="utf-8") as f:
    for file in part_files:
      abs_path = os.path.abspath(os.path.join(output_dir, file))
      # FFmpeg requires forward slashes on Windows paths in list files
      f.write(f"file '{abs_path.replace(os.sep, '/')}'\n")

  final_output_path = os.path.join(final_output_dir, "final_combined.mp3")

  # 3. Construct FFmpeg command
  # -f concat: uses the concat demuxer
  # -safe 0: allows absolute paths
  # -c copy: stream copy without re-encoding (instant and lossless)
  cmd = [
      "ffmpeg",
      "-y",
      "-f",
      "concat",
      "-safe",
      "0",
      "-i",
      list_file_path,
      "-c",
      "copy",
      final_output_path,
  ]

  print("Running FFmpeg to combine audio parts...")
  try:
    subprocess.run(
        cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    print(f"Success! Combined audio saved to: {final_output_path}")
  except subprocess.CalledProcessError as e:
    print(f"FFmpeg merging failed:\n{e.stderr.decode('utf-8', errors='ignore')}")
  except FileNotFoundError:
    print(
        "Error: 'ffmpeg' was not found in your system PATH. Please ensure"
        " FFmpeg is installed."
    )
  finally:
    # Cleanup temporary list file
    if os.path.exists(list_file_path):
      os.remove(list_file_path)


if __name__ == "__main__":
  combine_audio_parts()