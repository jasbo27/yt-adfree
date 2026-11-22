import re
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import quote_plus

import yt_dlp
from flask import Flask, Response, abort, jsonify, render_template_string, request, send_file

app = Flask(__name__)
DL_DIR = Path(__file__).parent / "downloads"
FMT = "bv*[vcodec^=avc1][height<=1080]+ba[ext=m4a]/bv*[height<=1080]+ba/b"
ID_RE = re.compile(r"^[\w-]{11}$")
jobs = {}  # id -> {"state": "downloading|done|error", "pct": float, "error": str}

HTML = """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YT Bez Reklam</title>
  <style>
    body { font-family: sans-serif; max-width: 800px; margin: 20px auto; background: #121212; color: #eee; padding: 0 15px; }
    input { width: 75%; padding: 10px; font-size: 16px; border-radius: 5px; border: none; }
    button { padding: 10px 15px; font-size: 16px; background: #e50914; color: #fff; border: none; border-radius: 5px; cursor: pointer; }
    video { width: 100%; margin-top: 20px; border-radius: 8px; background: #000; }
    .item { padding: 10px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
    a { color: #4ea8de; text-decoration: none; font-weight: bold; }
    .err { color: #ff6b6b; }
  </style>
</head>
<body>
  <h2>Odtwarzacz YT bez reklam</h2>
  <form method="get">
    <input type="text" name="q" placeholder="Wpisz frazę do wyszukania..." value="{{ q }}" required>
    <button type="submit">Szukaj</button>
  </form>

  {% if error %}<p class="err">{{ error }}</p>{% endif %}

  {% if v %}
    <h3>{{ title }}</h3>
    {% if mode == "stream" %}
      <video controls autoplay src="/stream?v={{ v }}"></video>
    {% else %}
      <p id="st">Przygotowuję…</p>
      <video id="vid" controls style="display:none"></video>
      <script>
        const v = "{{ v }}", st = document.getElementById("st"), vid = document.getElementById("vid");
        async function poll() {
          const j = await (await fetch("/status?v=" + v)).json();
          if (j.state === "done") { st.style.display = "none"; vid.style.display = "block"; vid.src = "/file/" + v; vid.play(); return; }
          if (j.state === "error") { st.className = "err"; st.textContent = "Błąd: " + j.error; return; }
          st.textContent = "Pobieranie… " + Math.round(j.pct) + "%";
          setTimeout(poll, 1000);
        }
        poll();
      </script>
    {% endif %}
  {% endif %}

  {% if results %}
    <h3>Wyniki wyszukiwania:</h3>
    {% for r in results %}
      <div class="item">
        <span>{{ r.title }} ({{ r.duration_string or '?' }})</span>
        <span><a href="/?v={{ r.id }}&q={{ q_enc }}">Odtwórz</a> · <a href="/?v={{ r.id }}&q={{ q_enc }}&mode=stream" style="font-weight:normal">Strumień</a></span>
      </div>
    {% endfor %}
  {% endif %}
</body>
</html>
"""


def get_title(v):
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        return ydl.extract_info(f"https://www.youtube.com/watch?v={v}", download=False, process=False).get("title")


@app.route("/stream")
def stream():
    v = request.args.get("v", "")
    if not ID_RE.match(v):
        abort(400)
    dl = subprocess.Popen(
        [sys.executable, "-m", "yt_dlp", "-q", "--no-warnings", "--remote-components", "ejs:github",
         "-f", FMT, "--retries", "5", "--fragment-retries", "5", "-o", "-",
         f"https://www.youtube.com/watch?v={v}"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    ff = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "frag_keyframe+empty_moov+default_base_moof", "-f", "mp4", "pipe:1"],
        stdin=dl.stdout, stdout=subprocess.PIPE)
    dl.stdout.close()

    def gen():
        try:
            yield from iter(lambda: ff.stdout.read(64 * 1024), b"")
        finally:
            ff.kill()
            dl.kill()

    return Response(gen(), mimetype="video/mp4")


def download(v):
    job = jobs[v] = {"state": "downloading", "pct": 0.0, "error": ""}
    DL_DIR.mkdir(exist_ok=True)

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if total:
                job["pct"] = min(99.0, d["downloaded_bytes"] / total * 100)

    opts = {
        "format": FMT, "quiet": True, "no_warnings": True, "merge_output_format": "mp4",
        "remote_components": ["ejs:github"], "retries": 5, "fragment_retries": 5,
        "outtmpl": str(DL_DIR / f"{v}.%(ext)s"), "progress_hooks": [hook],
        "postprocessor_args": {"merger": ["-c:v", "copy", "-c:a", "aac", "-b:a", "160k"]},
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={v}"])
        job["state"], job["pct"] = "done", 100.0
    except Exception as e:
        job["state"], job["error"] = "error", str(e)


@app.route("/status")
def status():
    v = request.args.get("v", "")
    if not ID_RE.match(v):
        abort(400)
    if (DL_DIR / f"{v}.mp4").exists() and jobs.get(v, {}).get("state") != "downloading":
        return jsonify(state="done", pct=100)
    if jobs.get(v, {}).get("state") in (None, "error"):
        threading.Thread(target=download, args=(v,), daemon=True).start()
        return jsonify(state="downloading", pct=0)
    return jsonify(jobs[v])


@app.route("/file/<v>")
def file(v):
    path = DL_DIR / f"{v}.mp4"
    if not ID_RE.match(v) or not path.exists():
        abort(404)
    return send_file(path, mimetype="video/mp4", conditional=True)


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    v = request.args.get("v", "").strip()
    mode = request.args.get("mode", "download")
    results, title, error = [], None, None
    if v and not ID_RE.match(v):
        v, error = "", "Nieprawidłowe ID filmu."

    try:
        if v:
            title = get_title(v)
        if q:
            with yt_dlp.YoutubeDL({"extract_flat": True, "quiet": True}) as ydl:
                results = ydl.extract_info(f"ytsearch10:{q}", download=False).get("entries", [])
    except Exception as e:
        error = f"Błąd: {e}"

    return render_template_string(
        HTML, q=q, v=v, q_enc=quote_plus(q), results=results,
        mode=mode, title=title, error=error,
    )


if __name__ == "__main__":
    app.run(port=5000)
