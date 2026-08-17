# app.py
#
# Two-step UI on purpose: generate the script first and let me read
# it before burning 2-3 minutes rendering a video. Early on I had it
# go straight from topic to finished video, and wasted a lot of
# render time on scripts I would've rewritten anyway.

import os
import streamlit as st

from graph import generate_script
from tts import generate_all_voiceovers
from render import render_video

st.set_page_config(page_title="Reel Generator", page_icon="🎬", layout="centered")

st.title("🎬 Reel Generator")
st.caption("Topic in, short-form vertical video out. Script → voiceover → captioned video.")

if "script" not in st.session_state:
    st.session_state.script = None

st.subheader("1. Write the script")
topic = st.text_input("Reel topic", placeholder="e.g. Why most beginners quit React Native in the first month")
tone = st.text_input("Tone", value="confident, a little blunt, no fluff")

if st.button("Generate script", type="primary") and topic:
    with st.spinner("Writing hook, scenes, and captions..."):
        st.session_state.script = generate_script(topic, tone)

if st.session_state.script:
    script = st.session_state.script

    st.subheader("2. Review before rendering")
    st.markdown(f"**Hook:** {script['hook']}")
    for i, n in enumerate(script["narrations"]):
        st.markdown(f"**Scene {i+1}:** {n}")
    st.markdown(f"**CTA:** {script['cta']}")

    with st.expander("Show on-screen captions"):
        st.write(script["hook_caption"])
        for c in script["scene_captions"]:
            st.write(c)
        st.write(script["cta_caption"])

    st.subheader("3. Render")
    if st.button("Generate video", type="primary"):
        work_dir = "output"
        audio_dir = os.path.join(work_dir, "audio")

        with st.spinner("Generating voiceover..."):
            narration_lines = [script["hook"]] + script["narrations"] + [script["cta"]]
            caption_lines = [script["hook_caption"]] + script["scene_captions"] + [script["cta_caption"]]
            voice_results = generate_all_voiceovers(narration_lines, audio_dir)

        lines_with_audio = [
            {"caption": caption_lines[i], "audio_path": v["path"], "duration": v["duration"]}
            for i, v in enumerate(voice_results)
        ]
        hook_line = lines_with_audio[0]
        cta_line = lines_with_audio[-1]
        scene_lines = lines_with_audio[1:-1]

        out_path = os.path.join(work_dir, "reel.mp4")
        with st.spinner("Rendering video (this takes a minute or two)..."):
            render_video(hook_line, scene_lines, cta_line, out_path)

        st.success("Done!")
        st.video(out_path)
        with open(out_path, "rb") as f:
            st.download_button("Download reel.mp4", f, file_name="reel.mp4")
