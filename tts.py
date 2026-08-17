# tts.py
#
# Using edge-tts instead of Gemini/OpenAI for voice on purpose -- it's
# free with no API key and no daily quota (I hit Gemini's 20/day free
# limit while building Interview Dojo, and didn't want the voice step
# eating into the same budget as the script-writing step). It's also
# just a genuinely good-sounding neural voice, which matters more here
# than in a chatbot since this audio goes straight into the final video.
#
# The real reason this file exists though: I don't trust word-count
# estimates for how long a line takes to speak (accents, punctuation
# pauses, and the TTS engine's own pacing all throw that off). So
# instead of guessing scene durations, every scene's audio actually
# gets generated first, and its *real* duration is measured from the
# file. render.py builds each scene to match that real number, not an
# estimate -- that's the only way the captions stay in sync with the
# voice.

import asyncio
import os
import edge_tts
from moviepy.editor import AudioFileClip

# a calm, confident voice -- browse more with `edge-tts --list-voices`
VOICE = "en-US-GuyNeural"


async def _synthesize(text: str, out_path: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(out_path)


def generate_voiceover(text: str, out_path: str) -> float:
    """Generates one audio file for a line of narration and returns
    its duration in seconds (measured, not estimated)."""
    asyncio.run(_synthesize(text, out_path))
    clip = AudioFileClip(out_path)
    duration = clip.duration
    clip.close()
    return duration


def generate_all_voiceovers(lines: list[str], out_dir: str) -> list[dict]:
    """Runs generate_voiceover for every line in the script (hook,
    each scene, cta) and returns [{path, duration}, ...] in order --
    render.py zips this straight up against the captions list."""
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for i, line in enumerate(lines):
        path = os.path.join(out_dir, f"line_{i:02d}.mp3")
        duration = generate_voiceover(line, path)
        results.append({"path": path, "duration": duration})
    return results
