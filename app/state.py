from typing import TypedDict, Any

class VideoState(TypedDict, total=False):
    request: str
    language: str
    duration_target: int
    script: str
    scenes: list[dict[str, Any]]
    voice_path: str
    voice_duration: float
    composition_html: str
    lint_report: str
    render_path: str
    error: str
