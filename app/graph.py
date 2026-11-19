import os
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from app.state import VideoState
from app.config import GEMINI_MODEL, PROJECT_DIR, WIDTH, HEIGHT, FPS, OUTPUT_DIR
from app.tools.llm import generate_storyboard, generate_composition
from app.tools.sarvam import make_voiceover
from app.tools.hyperframes import save_composition, lint_and_validate, render

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.35)

def plan_node(state: VideoState):
    plan = generate_storyboard(
        state["request"], state.get("language","Hindi/Hinglish"),
        int(state.get("duration_target",30))
    )
    return {"script": plan["script"], "scenes": plan["scenes"], "_storyboard": plan}

def voice_node(state: VideoState):
    audio_path = PROJECT_DIR / "assets" / "voice.wav"
    path, seconds = make_voiceover(state["script"], audio_path, state.get("language_code"))
    return {"voice_path": str(path), "voice_duration": seconds}

def compose_node(state: VideoState):
    storyboard = state.get("_storyboard") or {"title":"AI Video","scenes":state["scenes"]}
    html = generate_composition(
        state["request"], storyboard, state["voice_duration"],
        "assets/voice.wav", WIDTH, HEIGHT, FPS
    )
    save_composition(html)
    return {"composition_html": html}

def validate_node(state: VideoState):
    report = lint_and_validate()
    return {"lint_report": report}

def render_node(state: VideoState):
    path = render()
    return {"render_path": str(path)}

def build_graph():
    graph = StateGraph(VideoState)
    graph.add_node("plan", plan_node)
    graph.add_node("voiceover", voice_node)
    graph.add_node("compose", compose_node)
    graph.add_node("validate", validate_node)
    graph.add_node("render", render_node)
    graph.add_edge(START,"plan")
    graph.add_edge("plan","voiceover")
    graph.add_edge("voiceover","compose")
    graph.add_edge("compose","validate")
    graph.add_edge("validate","render")
    graph.add_edge("render",END)
    return graph.compile()
