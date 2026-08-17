# schemas.py
#
# Two schemas because the script gets built in two passes (see
# graph.py) -- first the raw narration, then a separate pass that
# condenses each narration line into a short on-screen caption.
# I split it this way after looking at my own Innera reels: what I
# *say* in a voiceover is never what looks good burned onto the
# screen as text. Narration can be a full sentence; captions need to
# be 4-6 words max or they get cut off / look cluttered on a phone
# screen. Trying to get one LLM call to write both well at once kept
# giving me either good narration with clunky captions, or punchy
# captions with narration that sounded like a tweet, not something
# a voiceover could read out.

from pydantic import BaseModel, Field
from typing import List


class ScriptScene(BaseModel):
    narration: str = Field(description="What the voiceover says for this scene, 1-2 natural sentences")


class DraftScript(BaseModel):
    hook: str = Field(description="The first line -- has to stop the scroll in under 2 seconds, no throat-clearing")
    scenes: List[ScriptScene] = Field(description="3 to 4 body scenes that deliver the actual content")
    cta: str = Field(description="Closing line -- what you want the viewer to do (follow, comment, save)")


class CaptionedScene(BaseModel):
    caption: str = Field(description="Short on-screen text for this scene, max 6 words, punchy, no filler words")


class CaptionSet(BaseModel):
    hook_caption: str = Field(description="On-screen version of the hook, max 6 words")
    scene_captions: List[CaptionedScene] = Field(description="One caption per body scene, same order as the scenes")
    cta_caption: str = Field(description="On-screen version of the CTA, max 6 words")
