import subprocess
from urllib.parse import quote_plus

import yt_dlp
from flask import Flask, Response, render_template_string, request

app = Flask(__name__)

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

  {% if stream_url %}
    <h3>{{ title }}</h3>
    <video controls autoplay src="/stream?v={{ v }}"></video>
  {% endif %}

  {% if results %}
    <h3>Wyniki wyszukiwania:</h3>
    {% for r in results %}
      <div class="item">
        <span>{{ r.title }} ({{ r.duration_string or '?' }})</span>
        <a href="/?v={{ r.id }}&q={{ q_enc }}">Odtwórz</a>
      </div>
    {% endfor %}
  {% endif %}
</body>
</html>
"""


@app.route("/")
def resolve(v):
    opts = {
        "format": "best[height<=1080]/best", "quiet": True, "no_warnings": True,
        "remote_components": ["ejs:github"],
        "extractor_args": {"youtube": {"player_client": ["web_safari"]}},
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(f"https://www.youtube.com/watch?v={v}", download=False)


@app.route("/stream")
def stream():
    info = resolve(request.args.get("v", ""))
    h = "".join(f"{k}: {val}\r\n" for k, val in (info.get("http_headers") or {}).items())
    cmd = ["ffmpeg", "-loglevel", "error", "-headers", h, "-i", info["url"], "-c", "copy",
           "-movflags", "frag_keyframe+empty_moov+default_base_moof", "-f", "mp4", "pipe:1"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    def gen():
        try:
            yield from iter(lambda: p.stdout.read(64 * 1024), b"")
        finally:
            p.kill()

    return Response(gen(), mimetype="video/mp4")


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    v = request.args.get("v", "").strip()
    results, stream_url, title, error = [], None, None, None

    try:
        if v:
            title = resolve(v).get("title")
            stream_url = True
        if q:
            with yt_dlp.YoutubeDL({"extract_flat": True, "quiet": True}) as ydl:
                results = ydl.extract_info(f"ytsearch10:{q}", download=False).get("entries", [])
    except Exception as e:
        error = f"Błąd: {e}"

    return render_template_string(
        HTML, q=q, v=v, q_enc=quote_plus(q), results=results,
        stream_url=stream_url, title=title, error=error,
    )


if __name__ == "__main__":
    app.run(port=5000)
