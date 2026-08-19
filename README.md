# Reel Generator

A topic goes in, a finished vertical (1080×1920) captioned reel comes
out. Script writing, multi-language localization, studio neural voiceover,
sound design, and video assembly are all automated -- built to actually
make high-retention reels for my Innera YouTube channel, not as a
portfolio-only demo.

## Why I built this

I already edit video for Innera, and the slow part was never the
editing -- it was staring at a blank page trying to write a hook
that doesn't sound like every other generic reel. I wanted something
that gives me a solid first draft (script + localized voiceover + SFX +
captioned rough cut) in under two minutes, that I can then review
and tweak, instead of starting from zero every single time.

## Pipeline


Topic + Language + Voice Gender
│
▼
[LangGraph: write_script]  ──► Generates spoken hook, body scenes, CTA
│
▼
[LangGraph: add_captions]  ──► Condenses each line into 2-4 word punchy captions
│
▼
[TTS Audio Engine]      ──► edge-tts synthesizes voiceover & measures exact durations
│
▼
[Pillow Engine]       ──► Renders Glassmorphism frames with Devanagari/Latin fonts
│
▼
[MoviePy Compositor]     ──► Stitches frames + voiceover + BGM + SFX into reel.mp4

## Features

- **Multi-Language Support:** Generate scripts & captions in **English**, **Hindi (हिन्दी)** with native Devanagari font rendering, or **Hinglish** (Hindi in Latin text).
- **Male & Female Neural Voices:** Tailored studio voices via `edge-tts` (`hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`, `en-US-AndrewMultilingualNeural`, `en-US-AvaMultilingualNeural`, etc.) with Reels-optimized speech pacing (`+10%` to `+12%`).
- **Glassmorphism UI:** Centered dark frosted-glass card, ambient dual aurora glow, floating contextual 3D emoji pill, and intelligent keyword highlighting.
- **Full Sound Design:** Dynamic transition whoosh SFX on scene changes combined with looped ambient background music (BGM).
- **Two-Step Review UI:** Streamlit interface allows reviewing and tweaking the generated script before burning time on video rendering.

## Why two separate LLM passes for the script

Narration and on-screen captions are two completely different jobs.
What sounds natural spoken out loud ("so here's the thing most people
get wrong about React Native performance...") is way too long to burn
onto a mobile screen as text. Trying to get one prompt to write both
well at once kept giving me either good narration with clunky captions,
or short punchy captions with narration that sounded like a tweet.

Splitting it into `write_script` (spoken narration) then `add_captions`
(condenses each line into a 2-4 word visual punch) fixed that -- see `graph.py`.

## Why scene duration comes from real audio, not word-count math

Word-count-based timing estimates (`words / 150wpm`) do not hold up --
punctuation pauses, accents, language variations (Devanagari vs English),
and the TTS engine's own pacing all throw that off. Every line's voiceover
is generated *first*, and its actual measured duration is what each video
frame holds for. That is the only way the captions stay in 100% sync with
the voice -- see `tts.py`.

## Visual style

Same palette as my portfolio -- copper (`#F0733C`), gold (`#FFC300`),
near-black (`#0A0A0C`), with the same two-glow aurora background effect.
Uses `Space Grotesk Bold` for English text with native OS font fallbacks
(`Nirmala UI`, `Mangal`) for crisp Hindi Devanagari rendering.

## Stack

- **LangGraph** -- 2-node state pipeline: `write_script` -> `add_captions`
- **Google Gemini (`gemini-2.5-flash`)** -- Structured output LLM for script & captions
- **edge-tts** -- Free neural TTS, no API key, no quota limits
- **Pillow (PIL)** -- Renders glassmorphism frames, font typography, and badges
- **MoviePy & NumPy** -- Stitches frames, voiceover, SFX, and BGM into final MP4
- **Streamlit** -- Interactive frontend for topic input, language/gender toggles, and review

## Setup & Installation

```bash
# 1. Clone repository & install dependencies
git clone [https://github.com/your-username/Reel_Generator.git](https://github.com/your-username/Reel_Generator.git)
cd Reel_Generator
pip install -r requirements.txt

# 2. Configure environment variables
cp .env.example .env
# Add your Gemini API key inside .env:
# GOOGLE_API_KEY=your_gemini_api_key_here

# 3. Optional assets setup:
# Drop custom font into assets/SpaceGrotesk-Bold.ttf
# Drop custom BGM tracks into assets/bgm/*.mp3

# 4. Run the Streamlit app
streamlit run app.py

Or run it headless for a single reel via CLI:
python pipeline.py

Real-life use
This is the first-draft generator for my Innera shorts -- topic in,
rough cut out, then I trim/adjust in an actual editor before posting.
It replaces the blank-page problem, not the whole editing process.
Roadmap
 * [x] Multi-language script generation (English, Hindi, Hinglish)
 * [x] Male / Female voice selector with Indian neural models
 * [x] Background music (BGM) integration & transition SFX
 * [x] Glassmorphism UI card styling
 * [ ] Word-by-word kinetic typography animation
 * [ ] Automated image/b-roll background generator per scene
 * [ ] Batch processing mode via CSV topic input