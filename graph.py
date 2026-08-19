# graph.py
#
# This one's a straight pipeline, not a loop like the Data Analyst
# Agent and not a multi-round back-and-forth like Interview Dojo --
# write_script always runs, then add_captions always runs after it.
# No branching. I still built it as a LangGraph instead of just two
# plain function calls because the state (topic, tone, language, hook, scenes,
# captions) needs to travel through both steps cleanly.

import os
from typing import TypedDict, List, Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from schemas import DraftScript, CaptionSet

load_dotenv()


class ReelState(TypedDict):
    topic: str
    tone: str
    language: str
    hook: Optional[str]
    narrations: Optional[List[str]]
    cta: Optional[str]
    hook_caption: Optional[str]
    scene_captions: Optional[List[str]]
    cta_caption: Optional[str]


def _llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0.7,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def write_script_node(state: ReelState) -> ReelState:
    lang = state.get("language", "English")

    lang_instruction = ""
    if "Hindi (हिन्दी)" in lang:
        lang_instruction = "CRITICAL: Write the entire script strictly in Hindi using Devanagari script (हिन्दी लिपि). Ensure natural spoken flow with pure Indian conversational rhythm."
    elif "Hinglish" in lang:
        lang_instruction = "CRITICAL: Write the entire script in Hinglish (Hindi words written using the English/Latin alphabet, e.g. 'Yeh galti har koi karta hai')."
    else:
        lang_instruction = "CRITICAL: Write the entire script in clear, punchy English."

    prompt = f"""Write a short-form vertical video script (like an Instagram Reel / YouTube Short) about: {state['topic']}

Tone: {state['tone']}
Language Rule: {lang_instruction}

Rules:
- Hook must work with zero context, first 2 seconds, no "hey guys welcome back"
- 3-4 body scenes, each one idea, written to be SPOKEN not read
- End with a clear one-line call to action
- Total spoken length should be under 40 seconds out loud"""

    llm = _llm().with_structured_output(DraftScript)
    draft: DraftScript = llm.invoke(prompt)

    state["hook"] = draft.hook
    state["narrations"] = [s.narration for s in draft.scenes]
    state["cta"] = draft.cta
    return state


def add_captions_node(state: ReelState) -> ReelState:
    scenes_block = "\n".join(f"{i+1}. {n}" for i, n in enumerate(state["narrations"]))
    lang = state.get("language", "English")

    lang_caption_rule = (
        "Write the captions in matching Hindi (Devanagari script)."
        if "Hindi (हिन्दी)" in lang
        else ("Write the captions in Hinglish (Roman English alphabet)." if "Hinglish" in lang else "Write the captions in English.")
    )

    prompt = f"""Here is a voiceover script. For each line, write a SHORT on-screen caption version (2-5 words max) -- these get burned onto the video as bold text, so they need to be scannable in under a second. Cut every word that isn't load-bearing.

Language Rule: {lang_caption_rule}

Hook (spoken): {state['hook']}
Body scenes (spoken):
{scenes_block}
CTA (spoken): {state['cta']}"""

    llm = _llm().with_structured_output(CaptionSet)
    captions: CaptionSet = llm.invoke(prompt)

    state["hook_caption"] = captions.hook_caption
    state["scene_captions"] = [c.caption for c in captions.scene_captions]
    state["cta_caption"] = captions.cta_caption
    return state


def build_graph():
    graph = StateGraph(ReelState)
    graph.add_node("write_script", write_script_node)
    graph.add_node("add_captions", add_captions_node)
    graph.set_entry_point("write_script")
    graph.add_edge("write_script", "add_captions")
    graph.add_edge("add_captions", END)
    return graph.compile()


_agent = build_graph()


def generate_script(topic: str, tone: str = "confident, no fluff", language: str = "English") -> ReelState:
    return _agent.invoke({
        "topic": topic,
        "tone": tone,
        "language": language,
        "hook": None,
        "narrations": None,
        "cta": None,
        "hook_caption": None,
        "scene_captions": None,
        "cta_caption": None,
    })