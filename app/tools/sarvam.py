import base64
from pathlib import Path
from sarvamai import SarvamAI
from app.config import SARVAM_TTS_MODEL, SARVAM_SPEAKER, SARVAM_LANGUAGE

def make_voiceover(text: str, output_path: Path, language_code: str | None = None) -> tuple[Path, float]:
    import os, subprocess
    key = os.getenv("SARVAM_API_KEY")
    if not key:
        raise RuntimeError("SARVAM_API_KEY is missing in .env")
    client = SarvamAI(api_subscription_key=key)
    lang = language_code or SARVAM_LANGUAGE
    # API currently limits Bulbul v3/v4-flash input to 2500 characters per request.
    chunks = [text[i:i+2400] for i in range(0, len(text), 2400)]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    part_paths = []
    for i, chunk in enumerate(chunks):
        result = client.text_to_speech.convert(
            text=chunk,
            model=SARVAM_TTS_MODEL,
            language_code=lang,
            speaker=SARVAM_SPEAKER,
            output_audio_codec="wav",
        )
        raw = base64.b64decode("".join(result.audios))
        part = output_path.parent / f"voice_part_{i}.wav"
        part.write_bytes(raw)
        part_paths.append(part)
    if len(part_paths) == 1:
        output_path.write_bytes(part_paths[0].read_bytes())
    else:
        concat_file = output_path.parent / "voice_concat.txt"
        concat_file.write_text("".join(f"file '{p.name}'\\n" for p in part_paths), encoding="utf-8")
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat_file),"-c:a","pcm_s16le",str(output_path)],check=True)
    for p in part_paths: p.unlink(missing_ok=True)
    probe = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(output_path)],capture_output=True,text=True,check=True)
    return output_path, float(probe.stdout.strip())
