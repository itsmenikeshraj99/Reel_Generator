# render.py
#
# The visual style here is deliberately the exact palette from my
# portfolio (copper #E07A3E, gold #D4A017, near-black #0D0D0D, same
# glow-blob background as aurora.css) instead of some generic
# stock-photo template. If these reels ever end up next to my
# portfolio link in a video description, they should look like they
# came from the same person -- that consistency was the whole point
# of picking a real brand palette earlier instead of a random
# gradient.
#
# Each scene is one still frame (caption + glow background) held for
# exactly as long as its voiceover line runs. I looked at doing full
# per-frame animation (text sliding in, background drifting) and
# decided against it for v1 -- a crossfade between static, well-
# designed frames reads as "clean," not "cheap," and it's a lot less
# that can break. Animation is on the roadmap, not a must-have.

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

W, H = 1080, 1920

BG = (13, 13, 13)
COPPER = (224, 122, 62)
GOLD = (212, 160, 23)
CREAM = (250, 243, 232)

FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "SpaceGrotesk-Bold.ttf")


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    # falls back to PIL's default bitmap font if the Space Grotesk
    # ttf isn't there -- ugly but it means the pipeline still runs
    # instead of crashing on a missing font file
    if os.path.exists(FONT_PATH):
        return ImageFont.truetype(FONT_PATH, size)
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_scene_frame(caption: str, accent: tuple = COPPER) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # two soft glow circles, same idea as the aurora background on
    # the portfolio -- one copper, one gold, so every reel frame
    # quietly echoes the site
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([-200, -300, 900, 700], fill=(*COPPER, 45))
    glow_draw.ellipse([300, 1200, 1400, 2200], fill=(*GOLD, 40))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = _load_font(92)
    max_text_width = W - 160
    lines = _wrap_text(draw, caption.upper(), font, max_text_width)

    line_height = 110
    total_height = line_height * len(lines)
    y = (H - total_height) // 2

    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (W - line_width) // 2
        draw.text((x, y), line, font=font, fill=CREAM)
        y += line_height

    # a small accent bar under the text -- copper for body scenes,
    # gold for hook/cta so the two "important" frames stand out
    bar_w = 90
    bar_y = y + 20
    draw.rectangle([(W - bar_w) // 2, bar_y, (W + bar_w) // 2, bar_y + 6], fill=accent)

    return img


def render_video(hook_line: dict, scene_lines: list[dict], cta_line: dict, out_path: str):
    """hook_line / cta_line / each item in scene_lines look like:
    {"caption": str, "audio_path": str, "duration": float}"""

    frames_dir = os.path.join(os.path.dirname(out_path), "_frames")
    os.makedirs(frames_dir, exist_ok=True)

    clips = []
    all_lines = [("hook", hook_line, GOLD)] + [("scene", s, COPPER) for s in scene_lines] + [("cta", cta_line, GOLD)]

    for i, (kind, line, accent) in enumerate(all_lines):
        frame = make_scene_frame(line["caption"], accent=accent)
        frame_path = os.path.join(frames_dir, f"frame_{i:02d}.png")
        frame.save(frame_path)

        clip = ImageClip(frame_path).set_duration(line["duration"])
        clip = clip.set_audio(AudioFileClip(line["audio_path"]))
        clip = clip.crossfadein(0.25 if i > 0 else 0)
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose", padding=-0.25)
    final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac")

    for c in clips:
        c.close()
