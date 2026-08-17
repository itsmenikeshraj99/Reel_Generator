# pipeline.py
#
# Glue code -- takes a topic all the way from "script idea" to
# "finished mp4 on disk". Kept separate from app.py so this same
# function could later run from a plain CLI script or a scheduled
# job (e.g. "generate 3 reels every Monday for Innera") without
# dragging Streamlit into it.

import os
import shutil
from graph import generate_script
from tts import generate_all_voiceovers
from render import render_video


def build_reel(topic: str, tone: str, work_dir: str = "output") -> str:
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    print(f"[1/3] Writing script for: {topic}")
    script = generate_script(topic, tone)

    # flatten hook + scenes + cta into one ordered list so TTS and
    # captions line up by index without any special-casing
    narration_lines = [script["hook"]] + script["narrations"] + [script["cta"]]
    caption_lines = [script["hook_caption"]] + script["scene_captions"] + [script["cta_caption"]]

    print(f"[2/3] Generating voiceover ({len(narration_lines)} lines)")
    audio_dir = os.path.join(work_dir, "audio")
    voice_results = generate_all_voiceovers(narration_lines, audio_dir)

    lines_with_audio = [
        {"caption": caption_lines[i], "audio_path": v["path"], "duration": v["duration"]}
        for i, v in enumerate(voice_results)
    ]

    hook_line = lines_with_audio[0]
    cta_line = lines_with_audio[-1]
    scene_lines = lines_with_audio[1:-1]

    print("[3/3] Rendering video")
    out_path = os.path.join(work_dir, "reel.mp4")
    render_video(hook_line, scene_lines, cta_line, out_path)

    print(f"Done -> {out_path}")
    return out_path


if __name__ == "__main__":
    build_reel(
        topic="Why most beginners quit React Native in the first month",
        tone="confident, a little blunt, no fluff",
    )
