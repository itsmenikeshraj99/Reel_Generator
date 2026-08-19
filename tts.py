# tts.py
import asyncio
import os
import re
import edge_tts
from moviepy.editor import AudioFileClip

# Neural Voice Matrix (Language + Gender)
VOICE_CATALOG = {
    "hindi": {
        "male": "hi-IN-MadhurNeural",       # Deep, professional Hindi male narrator
        "female": "hi-IN-SwaraNeural",     # Clear, modern Hindi female narrator
    },
    "english": {
        "male": "en-US-AndrewMultilingualNeural", # Studio quality English male
        "female": "en-US-AvaMultilingualNeural",  # Natural expressive English female
    },
    "hinglish": {
        "male": "en-IN-PrabhatNeural",     # Indian accent English/Hinglish male
        "female": "en-IN-NeerjaNeural",    # Indian accent English/Hinglish female
    }
}

VOICE_RATE = "+10%"


def _resolve_voice(language: str, gender: str) -> str:
    lang_key = "english"
    if "Hindi" in language:
        lang_key = "hindi"
    elif "Hinglish" in language:
        lang_key = "hinglish"

    gen_key = "female" if "Female" in gender else "male"
    return VOICE_CATALOG.get(lang_key, {}).get(gen_key, "en-US-AndrewMultilingualNeural")


async def _synthesize(text: str, out_path: str, voice: str, rate: str = VOICE_RATE):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(out_path)


def generate_voiceover(text: str, out_path: str, voice: str) -> float:
    try:
        asyncio.run(_synthesize(text, out_path, voice=voice))
    except Exception as e:
        print(f"[Warning] Voice failed ({e}), using default fallback...")
        fallback = edge_tts.Communicate(text=text, voice="hi-IN-MadhurNeural", rate="+5%")
        asyncio.run(fallback.save(out_path))

    clip = AudioFileClip(out_path)
    duration = clip.duration
    clip.close()
    return duration


def generate_all_voiceovers(lines: list[str], out_dir: str, language: str = "English", gender: str = "Male") -> list[dict]:
    os.makedirs(out_dir, exist_ok=True)
    results = []

    selected_voice = _resolve_voice(language, gender)
    print(f"[Audio Engine] Voice Config: {language} | {gender} -> {selected_voice}")

    for i, line in enumerate(lines):
        path = os.path.join(out_dir, f"line_{i:02d}.mp3")
        duration = generate_voiceover(line, path, voice=selected_voice)
        results.append({"path": path, "duration": duration})

    return results
