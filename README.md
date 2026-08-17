# Reel Generator

A topic goes in, a finished vertical (1080×1920) captioned reel comes
out. Script writing, voiceover, and video assembly are all automated
-- built to actually make reels for my Innera YouTube channel, not
as a portfolio-only demo.

## Why I built this

I already edit video for Innera, and the slow part was never the
editing -- it was staring at a blank page trying to write a hook
that doesn't sound like every other "5 tips for..." reel. I wanted
something that gives me a solid first draft (script + voice + a
rough cut) in under two minutes, that I can then tweak, instead of
starting from nothing every time.

## Pipeline

```
topic --> [write_script] --> [add_captions] --> voiceover (edge-tts)
                                                       |
                                                       v
                                          per-line audio duration measured
                                                       |
                                                       v
                                        render.py builds one frame per line
                                                       |
                                                       v
                                          moviepy stitches it into reel.mp4
```

## Why two separate LLM passes for the script

Narration and on-screen captions are different jobs. What sounds
natural spoken out loud ("so here's the thing most people get wrong
about React Native performance...") is way too long to burn onto a
screen as text. Trying to get one prompt to write both well at once
kept giving me either good narration with clunky captions, or short
punchy captions with narration that sounded like a tweet. Splitting
it into `write_script` (narration) then `add_captions` (condenses
each line separately) fixed that -- see `graph.py`.

## Why scene duration comes from real audio, not word-count math

Word-count-based timing estimates (words / 150wpm) don't hold up --
punctuation pauses, the TTS engine's own pacing, and how a sentence
is phrased all throw it off. Every line's voiceover is generated
*first*, and its actual measured duration is what each video frame
holds for. That's the only way the captions stay in sync with the
voice -- see `tts.py`.

## Visual style

Same palette as my portfolio -- copper, gold, near-black, with the
same two-glow-blob background as the site's aurora effect, and the
same Space Grotesk font used for headings there. If a reel and my
portfolio link end up in the same video description, they should
look like they came from the same person.

## Stack
- **LangGraph** -- 2-node pipeline: write_script -> add_captions
- **Google Gemini (`gemini-flash-latest`)** -- free-tier LLM, script + captions
- **edge-tts** -- free neural TTS, no API key, no quota (keeps this
  independent of the Gemini free-tier limit)
- **Pillow** -- renders each caption frame
- **MoviePy** -- stitches frames + audio into the final mp4
- **Streamlit** -- script review + render UI

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# add your free Gemini key: https://aistudio.google.com/apikey

# optional but recommended: drop a Space Grotesk Bold .ttf into
# assets/SpaceGrotesk-Bold.ttf (see assets/README.txt)

streamlit run app.py
```

Or run it headless for a single reel:

```bash
python pipeline.py
```

## Real-life use

This is the first-draft generator for my Innera shorts -- topic in,
rough cut out, then I trim/adjust in an actual editor before posting.
It replaces the blank-page problem, not the whole editing process.

## Next steps
- [ ] Light per-frame animation (word-by-word caption reveal) instead of static frames
- [ ] Background music bed, ducked under the voiceover
- [ ] Batch mode: feed a list of topics, get a folder of drafts
