# render.py
import os
import glob
import random
import re
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    AudioClip,
    CompositeAudioClip,
    CompositeVideoClip,
    concatenate_videoclips,
    afx
)

W, H = 1080, 1920

# Brand Aesthetics Palette
BG_DARK = (10, 10, 12)
CARD_BG = (22, 22, 26, 215)
CARD_BORDER = (245, 180, 0, 75)
COPPER = (240, 115, 60)
GOLD = (255, 195, 0)
CREAM = (255, 255, 255)
MUTED_TEXT = (170, 170, 180)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
BGM_DIR = os.path.join(ASSETS_DIR, "bgm")
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")
FONT_PATH = os.path.join(ASSETS_DIR, "SpaceGrotesk-Bold.ttf")

STOP_WORDS = {
    "THE", "IS", "AND", "A", "AN", "IN", "ON", "FOR", "TO", "OF",
    "WITH", "AT", "BY", "THIS", "THAT", "YOUR", "OUR", "ARE", "AS",
    "BE", "WHAT", "WHEN", "WHERE", "WHO", "WHY", "HOW", "THEIR",
    "THEM", "THEY", "IT", "ITS", "INTO", "OVER", "UNDER", "ABOUT",
    "JUST", "ALSO", "EVEN", "MORE", "LESS", "ONLY", "BEEN", "HAVE",
    "HAS", "HAD", "WILL", "WOULD", "COULD", "SHOULD", "CAN", "WAS",
    "WERE", "NOT", "DONT", "DOESNT", "WE", "YOU", "MY", "ME", "ALL",
    # Hindi Stop Words
    "है", "हैं", "का", "की", "के", "में", "पर", "से", "को", "और",
    "यह", "वह", "भी", "तो", "ही", "कर", "रहा", "रही", "रहे", "होता", "होती"
}

EMOJI_KEYWORDS = {
    "PAYCHECK": "💸", "GROCERY": "🛒", "FOOD": "🌾", "DROUGHTS": "☀️",
    "HEAT": "🌡️", "HEALTH": "🫀", "STORMS": "🌪️", "HOMES": "🏠",
    "CLIMATE": "🌍", "WARMING": "🔥", "MONEY": "💰", "CODE": "💻",
    "REACT": "⚡", "BUG": "🐛", "INSIGHT": "💡", "FOLLOW": "🔔",
    "HOOK": "🎯", "DESTROYING": "⚠️", "PROTECT": "🛡️", "WILDLIFE": "🐾",
    "पेड़": "🌳", "जंगल": "🌲", "जानवर": "🐾", "पानी": "💧", "खतरा": "⚠️"
}


def _create_synthetic_sfx(path: str, kind: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if kind == "whoosh":
        def make_whoosh(t):
            freq = 450 - 320 * (t / 0.22)
            envelope = np.sin(np.pi * (t / 0.22))
            noise = np.random.uniform(-0.15, 0.15, size=t.shape if isinstance(t, np.ndarray) else 1)
            sig = (np.sin(2 * np.pi * freq * t) * 0.4 + noise) * envelope
            return np.array([sig, sig]).T if isinstance(sig, np.ndarray) else np.array([sig, sig])
        clip = AudioClip(make_whoosh, duration=0.22)
        clip.write_audiofile(path, fps=44100, logger=None)


def ensure_media_assets():
    os.makedirs(BGM_DIR, exist_ok=True)
    os.makedirs(SFX_DIR, exist_ok=True)

    default_bgm = {
        "lofi_chill.mp3": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
        "tech_beat.mp3": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    for filename, url in default_bgm.items():
        dest = os.path.join(BGM_DIR, filename)
        if not os.path.exists(dest):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=3) as res, open(dest, 'wb') as f:
                    f.write(res.read())
            except Exception:
                pass

    whoosh_path = os.path.join(SFX_DIR, "whoosh.mp3")
    if not os.path.exists(whoosh_path):
        _create_synthetic_sfx(whoosh_path, "whoosh")


def _is_hindi_text(text: str) -> bool:
    return bool(re.search(r'[\u0900-\u097F]', text))


def _load_font(size: int, is_hindi: bool = False, emoji: bool = False) -> ImageFont.FreeTypeFont:
    if emoji:
        for ef in ["C:\\Windows\\Fonts\\seguiemj.ttf", "Apple Color Emoji.ttf"]:
            if os.path.exists(ef):
                try:
                    return ImageFont.truetype(ef, size)
                except Exception:
                    pass

    # Windows Native Hindi/Devanagari Fonts
    if is_hindi:
        hindi_fonts = [
            "C:\\Windows\\Fonts\\NirmalaB.ttf",
            "C:\\Windows\\Fonts\\Nirmala.ttf",
            "C:\\Windows\\Fonts\\mangal.ttf",
            "C:\\Windows\\Fonts\\aparaj.ttf"
        ]
        for hf in hindi_fonts:
            if os.path.exists(hf):
                try:
                    return ImageFont.truetype(hf, size)
                except Exception:
                    continue

    # English Fonts
    if os.path.exists(FONT_PATH):
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            pass

    fallback_fonts = [
        "C:\\Windows\\Fonts\\NirmalaB.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "arial.ttf",
    ]
    for f in fallback_fonts:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue

    return ImageFont.load_default()


def _wrap_text_into_word_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[list[str]]:
    words = text.split()
    lines, current_line = [], []
    for word in words:
        trial = " ".join(current_line + [word])
        if draw.textlength(trial, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(current_line)
            current_line = [word]
    if current_line:
        lines.append(current_line)
    return lines


def _detect_emoji(text: str, badge: str) -> str:
    combined = f"{text.upper()} {badge.upper()}"
    for k, emoji in EMOJI_KEYWORDS.items():
        if k in combined:
            return emoji
    return "⚡"


def make_scene_frame(caption: str, tag_text: str = "INSIGHT", accent: tuple = COPPER, progress_pct: float = 0.0) -> Image.Image:
    img = Image.new("RGB", (W, H), BG_DARK)
    is_hindi = _is_hindi_text(caption)

    # 1. Background Aurora Glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([-220, -180, 1050, 750], fill=(*COPPER, 65))
    glow_draw.ellipse([180, 1150, 1480, 2250], fill=(*GOLD, 50))
    glow = glow.filter(ImageFilter.GaussianBlur(135))
    img = Image.alpha_composite(img.convert("RGBA"), glow)

    # 2. Glassmorphism Card Frame
    card_w, card_h = 920, 840
    card_x1 = (W - card_w) // 2
    card_y1 = (H - card_h) // 2 - 20
    card_x2 = card_x1 + card_w
    card_y2 = card_y1 + card_h

    card_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=44, fill=CARD_BG, outline=CARD_BORDER, width=2)
    img = Image.alpha_composite(img, card_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 3. Floating 3D Emoji
    active_emoji = _detect_emoji(caption, tag_text)
    emoji_font = _load_font(48, emoji=True)
    emoji_box_w = 104
    emoji_box = [(W - emoji_box_w) // 2, card_y1 - 52, (W + emoji_box_w) // 2, card_y1 + 52]
    draw.rounded_rectangle(emoji_box, radius=52, fill=(18, 18, 22), outline=accent, width=2)
    draw.text((W // 2, card_y1), active_emoji, font=emoji_font, anchor="mm", embedded_color=True)

    # 4. Top Category Badge Inside Card
    tag_font = _load_font(36, is_hindi=False)
    full_tag = f"•  {tag_text.upper()}  •"
    tag_w = draw.textlength(full_tag, font=tag_font)
    draw.text(((W - tag_w) // 2, card_y1 + 75), full_tag, font=tag_font, fill=accent)

    # 5. Text & Keyword Highlight
    raw_words = caption.split()
    eligible = [w.strip(".,!?:;\"'()[]{}|") for w in raw_words if w.upper().strip(".,!?:;\"'()[]{}|") not in STOP_WORDS]
    highlight_targets = set(sorted(eligible, key=len, reverse=True)[:2]) if len(eligible) >= 2 else set(eligible)

    # Hindi script rendering
    font_size = 68 if is_hindi else 74
    main_font = _load_font(font_size, is_hindi=is_hindi)
    display_text = caption if is_hindi else caption.upper()

    max_text_width = card_w - 120
    word_lines = _wrap_text_into_word_lines(draw, display_text, main_font, max_text_width)

    line_height = 110 if is_hindi else 104
    total_height = line_height * len(word_lines)
    y = card_y1 + 160 + ((card_h - 260) - total_height) // 2
    space_w = draw.textlength(" ", font=main_font)

    for line_words in word_lines:
        line_word_widths = [draw.textlength(w, font=main_font) for w in line_words]
        line_w = sum(line_word_widths) + space_w * (len(line_words) - 1)
        cur_x = (W - line_w) // 2

        for word, w_len in zip(line_words, line_word_widths):
            clean_word = word.strip(".,!?:;\"'()[]{}|")
            is_highlight = clean_word in highlight_targets or clean_word.upper() in highlight_targets
            color = GOLD if is_highlight else CREAM

            draw.text((cur_x + 3, y + 4), word, font=main_font, fill=(0, 0, 0, 230))
            draw.text((cur_x, y), word, font=main_font, fill=color)
            cur_x += w_len + space_w

        y += line_height

    # 6. Bottom Accent Underline Bar
    bar_w = 100
    bar_y = card_y2 - 55
    draw.rounded_rectangle([(W - bar_w) // 2, bar_y, (W + bar_w) // 2, bar_y + 6], radius=3, fill=accent)

    # 7. Progress Bar
    draw.rectangle([0, H - 14, W, H], fill=(28, 28, 34))
    progress_w = int(W * progress_pct)
    if progress_w > 0:
        draw.rectangle([0, H - 14, progress_w, H], fill=GOLD)

    return img


def pick_smart_bgm() -> str | None:
    if not os.path.exists(BGM_DIR):
        return None
    all_tracks = glob.glob(os.path.join(BGM_DIR, "*.mp3"))
    return random.choice(all_tracks) if all_tracks else None


def render_video(hook_line: dict, scene_lines: list[dict], cta_line: dict, out_path: str):
    ensure_media_assets()

    frames_dir = os.path.join(os.path.dirname(out_path), "_frames")
    os.makedirs(frames_dir, exist_ok=True)

    all_lines = (
        [("HOOK", hook_line, GOLD)] +
        [("INSIGHT", s, COPPER) for s in scene_lines] +
        [("FOLLOW", cta_line, GOLD)]
    )

    total_scenes = len(all_lines)
    clips = []
    sfx_clips = []
    current_time = 0.0

    whoosh_file = os.path.join(SFX_DIR, "whoosh.mp3")

    for i, (badge, line, accent) in enumerate(all_lines):
        dur = line["duration"]
        progress_pct = (i + 1) / total_scenes

        frame = make_scene_frame(line["caption"], tag_text=badge, accent=accent, progress_pct=progress_pct)
        frame_path = os.path.join(frames_dir, f"frame_{i:02d}.png")
        frame.save(frame_path)

        clip = ImageClip(frame_path).set_duration(dur)
        clip = clip.set_audio(AudioFileClip(line["audio_path"]))
        clips.append(clip)

        if i > 0 and os.path.exists(whoosh_file):
            try:
                sfx = AudioFileClip(whoosh_file).fx(afx.volumex, 0.18).set_start(current_time - 0.08)
                sfx_clips.append(sfx)
            except Exception:
                pass

        current_time += dur

    final_video = concatenate_videoclips(clips, method="compose")
    audio_layers = [final_video.audio] + sfx_clips

    selected_bgm = pick_smart_bgm()
    if selected_bgm and os.path.exists(selected_bgm):
        try:
            bgm = AudioFileClip(selected_bgm).fx(afx.volumex, 0.07)
            bgm = afx.audio_loop(bgm, duration=final_video.duration)
            audio_layers.append(bgm)
        except Exception:
            pass

    final_video = final_video.set_audio(CompositeAudioClip(audio_layers))
    final_video = final_video.set_duration(current_time)

    final_video.write_videofile(
        out_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=8,
        logger=None
    )

    for c in clips:
        c.close()