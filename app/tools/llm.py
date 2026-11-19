import json
import html as html_lib
from json import JSONDecodeError

from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GEMINI_MODEL

llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.2)


def _response_text(response) -> str:
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get('text'), str):
                parts.append(block['text'])
            elif isinstance(block, str):
                parts.append(block)
        return '\n'.join(parts)
    return str(content)


def parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith('```'):
        lines = raw.splitlines()
        if lines and lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith('```'):
            lines = lines[:-1]
        raw = '\n'.join(lines).strip()

    start = raw.find('{')
    if start < 0:
        raise ValueError('Gemini response does not contain a JSON object')
    data, _ = json.JSONDecoder().raw_decode(raw[start:])
    if not isinstance(data, dict):
        raise ValueError('Gemini response must be a JSON object')
    return data


def generate_storyboard(request: str, language: str, duration: int) -> dict:
    prompt = f'''You are a professional short-form video director.
Create a storyboard for this video.
User request: {request}
Language: {language}
Target duration: {duration} seconds.

Return ONLY valid JSON. Do not use Markdown fences or explanations.
Use double quotes for all JSON keys and string values.
Required structure:
{{
  "title": "Video title",
  "script": "Complete spoken narration",
  "scenes": [
    {{
      "duration": 10,
      "visual_description": "Scene description",
      "on_screen_text": "Short text",
      "threejs_object": "sphere"
    }}
  ]
}}
Rules:
- Use 3 to 7 scenes.
- Scene durations should add up approximately to {duration} seconds.
- Narration must be natural and suitable for speech.
- Use Hindi when Hindi is requested.
- threejs_object must be one of: sphere, torus, icosahedron, particles.
'''
    raw = _response_text(llm.invoke(prompt))
    try:
        data = parse_json_response(raw)
    except (JSONDecodeError, ValueError):
        repair_prompt = f'''Convert the following response into valid JSON.
Return ONLY JSON with double-quoted keys and strings. No Markdown or explanation.
Required keys: title, script, scenes. Preserve the original information.
Original response:
{raw}'''
        repaired_raw = _response_text(llm.invoke(repair_prompt))
        data = parse_json_response(repaired_raw)

    if not data.get('title') or not data.get('script'):
        raise ValueError('Gemini returned an incomplete storyboard')
    scenes = data.get('scenes')
    if not isinstance(scenes, list) or not scenes:
        raise ValueError('Gemini did not return a valid scenes list')
    for scene in scenes:
        if not isinstance(scene, dict) or 'duration' not in scene:
            raise ValueError('A scene is invalid or missing duration')
        scene['duration'] = float(scene['duration'])
    return data


def generate_composition(request: str, storyboard: dict, voice_duration: float,
                         voice_relpath: str, width: int, height: int, fps: int) -> str:
    # Build the composition deterministically from structured scene data.
    # Gemini is used for creative planning; generated code is not executed from raw model output.
    scenes_json = json.dumps(storyboard["scenes"], ensure_ascii=False).replace("</", "<\\/")
    title = json.dumps(storyboard.get("title", "AI Video"))
    safe_title = html_lib.escape(str(storyboard.get("title", "AI Video")))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{box-sizing:border-box}} html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#080d1b;color:#fff;font-family:Arial,sans-serif}}
#root{{position:relative;width:{width}px;height:{height}px;overflow:hidden;background:radial-gradient(circle at 50% 35%,#18345b,#080d1b 68%)}}
#three-layer{{position:absolute;inset:0;width:100%;height:100%;z-index:0}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(2,6,23,.1),rgba(2,6,23,.88));z-index:1}}
.copy{{position:absolute;left:8%;right:8%;bottom:17%;z-index:2;text-align:center}}
.kicker{{font-size:24px;letter-spacing:8px;text-transform:uppercase;color:#7dd3fc;margin-bottom:28px}}
h1{{font-size:76px;line-height:1.08;margin:0 0 22px;font-weight:800;text-shadow:0 8px 40px #000}}
p{{font-size:34px;line-height:1.35;color:#dbeafe;margin:0}}
.pill{{display:inline-block;margin-top:32px;padding:12px 24px;border:1px solid #7dd3fc;border-radius:999px;color:#bae6fd;font-size:20px}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{max(1.0, voice_duration):.3f}" data-width="{width}" data-height="{height}">
  <canvas id="three-layer"></canvas>
  <div class="shade"></div>
  <div class="copy">
    <div class="kicker">A short story for you</div>
    <h1 id="headline"></h1>
    <p id="subline"></p>
    <div class="pill">Keep moving forward</div>
  </div>
  <audio
    id="voice-audio"
    src="{voice_relpath}"
    data-start="0"
    data-duration="{voice_duration:.3f}"
    data-track-index="9"
></audio>
</div>
<script type="module">
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.181.2/+esm";
const W={width}, H={height};
const canvas=document.querySelector("#three-layer");
const renderer=new THREE.WebGLRenderer({{canvas,alpha:true,antialias:true}});
renderer.setSize(W,H,false); renderer.setPixelRatio(1);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(38,W/H,0.1,100);
camera.position.set(0,0,7);
scene.add(new THREE.HemisphereLight(0xffffff,0x172554,2.0));
const key=new THREE.PointLight(0x7dd3fc,45,30); key.position.set(3,4,5); scene.add(key);
const geometry=new THREE.IcosahedronGeometry(1.55,2);
const material=new THREE.MeshStandardMaterial({{color:0x38bdf8,metalness:.55,roughness:.22,wireframe:false}});
const orb=new THREE.Mesh(geometry,material); scene.add(orb);
const wire=new THREE.Mesh(new THREE.IcosahedronGeometry(1.8,1),new THREE.MeshBasicMaterial({{color:0x93c5fd,wireframe:true,transparent:true,opacity:.24}})); scene.add(wire);
const particles=new THREE.Points(new THREE.BufferGeometry(),new THREE.PointsMaterial({{color:0xc4b5fd,size:.025,transparent:true,opacity:.8}}));
const positions=[];
let seed=20261119; function seeded(){{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}} for(let i=0;i<450;i++){{const r=2.2+seeded()*2.8;const a=seeded()*Math.PI*2;const b=Math.acos(2*seeded()-1);positions.push(r*Math.sin(b)*Math.cos(a),r*Math.sin(b)*Math.sin(a),r*Math.cos(b));}}
particles.geometry.setAttribute("position",new THREE.Float32BufferAttribute(positions,3));scene.add(particles);
function renderAt(t){{
  orb.rotation.x=t*.22; orb.rotation.y=t*.48;
  wire.rotation.x=-t*.12; wire.rotation.y=t*.2;
  particles.rotation.y=t*.035;
  const pulse=1+Math.sin(t*1.7)*.035; orb.scale.setScalar(pulse);
  renderer.render(scene,camera);
}}
window.addEventListener("hf-seek",(e)=>renderAt(e.detail.time));
renderAt(0);
const headline=document.querySelector("#headline");
const subline=document.querySelector("#subline");
const scenes={scenes_json};
const total={max(1.0, voice_duration):.3f};
const timeline=gsap.timeline({{paused:true}});
let cursor=0;
for(const item of scenes){{
  const start=cursor;
  const dur=Math.max(.5,Number(item.duration)||2);
  timeline.call(()=>{{headline.textContent=item.on_screen_text||{title};subline.textContent=item.visual_description||"";}},[],start);
  timeline.fromTo(".copy",{{opacity:0,y:35}},{{opacity:1,y:0,duration:.55,ease:"power3.out"}},start);
  timeline.to(".copy",{{opacity:0,y:-15,duration:.35}},start+Math.max(.55,dur-.4));
  cursor+=dur;
}}
window.__timelines=window.__timelines||{{}};
window.__timelines["main"]=timeline;
</script>
</body>
</html>'''

