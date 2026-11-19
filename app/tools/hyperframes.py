
import os
import shutil
import subprocess
from pathlib import Path

from app.config import PROJECT_DIR, OUTPUT_DIR


def _run(args: list[str], timeout: int = 900, cwd=None) -> str:
    command = (
        subprocess.list2cmdline(args)
        if os.name == "nt"
        else args
    )

    p = subprocess.run(
        command,
        cwd=cwd or PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=(os.name == "nt"),
    )

    output = (p.stdout or "") + (p.stderr or "")

    if p.returncode:
        raise RuntimeError(
            f"Command failed ({p.returncode}): {' '.join(args)}\n"
            f"{output[-5000:]}"
        )

    return output


def ensure_project() -> None:
    if not (PROJECT_DIR / "index.html").exists():
        PROJECT_DIR.parent.mkdir(parents=True, exist_ok=True)

        _run(
            ["npx", "-y", "hyperframes", "init", PROJECT_DIR.name],
            timeout=300,
            cwd=PROJECT_DIR.parent,
        )

    (PROJECT_DIR / "assets").mkdir(parents=True, exist_ok=True)


def save_composition(html: str) -> Path:
    ensure_project()
    path = PROJECT_DIR / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def lint_and_validate() -> str:
    lint = _run(
        ["npx", "-y", "hyperframes", "lint"],
        timeout=180,
    )
    return lint[-5000:] or "HyperFrames lint passed."


def render() -> Path:
    _run(
        ["npx", "-y", "hyperframes", "render"],
        timeout=3600,
    )

    renders = PROJECT_DIR / "renders"
    candidates = (
        sorted(renders.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if renders.exists()
        else []
    )

    if not candidates:
        raise RuntimeError(
            "Render completed but no MP4 was found in renders/"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUTPUT_DIR / candidates[-1].name
    shutil.copy2(candidates[-1], dest)

    return dest
