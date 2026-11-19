import argparse
from dotenv import load_dotenv
from app.graph import build_graph
from app.tools.hyperframes import ensure_project

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Generate a video using Gemini + Sarvam + Three.js + HyperFrames")
    parser.add_argument("--prompt", required=True, help="What video should the agent create?")
    parser.add_argument("--duration", type=int, default=30, help="Target duration in seconds")
    parser.add_argument("--language", default="Hindi/Hinglish", help="Narration language")
    parser.add_argument("--language-code", default="hi-IN", help="Sarvam BCP-47 language code")
    args = parser.parse_args()
    ensure_project()
    app = build_graph()
    result = app.invoke({
        "request": args.prompt,
        "duration_target": args.duration,
        "language": args.language,
        "language_code": args.language_code,
    })
    print("\\nVIDEO GENERATED")
    print("Script:", result.get("script",""))
    print("Voice duration:", result.get("voice_duration"))
    print("Output:", result.get("render_path"))

if __name__ == "__main__":
    main()
