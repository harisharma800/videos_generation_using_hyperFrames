import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = (ROOT / os.getenv("VIDEO_PROJECT_DIR", "video_project")).resolve()
OUTPUT_DIR = (ROOT / os.getenv("OUTPUT_DIR", "outputs")).resolve()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
SARVAM_SPEAKER = os.getenv("SARVAM_SPEAKER", "shubh")
SARVAM_LANGUAGE = os.getenv("SARVAM_LANGUAGE", "hi-IN")
WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
FPS = int(os.getenv("VIDEO_FPS", "30"))
