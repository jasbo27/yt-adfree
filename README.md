# YT Bez Reklam

Kompaktowa aplikacja webowa (Flask + yt-dlp): wyszukuje filmy w YouTube i odtwarza je w przeglądarce bez reklam. Cały kod to jeden plik `app.py`.

## Uruchomienie (uv – zalecane)

```bash
git clone https://github.com/jasbo27/yt-adfree.git
cd yt-adfree
uv run --with flask --with yt-dlp app.py
```

## Alternatywa: pip

```bash
git clone https://github.com/jasbo27/yt-adfree.git
cd yt-adfree
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Następnie otwórz <http://127.0.0.1:5000>.

## Wymagania

Python 3.9+ oraz środowisko JavaScript (`deno` lub `node`) – yt-dlp potrzebuje go do odszyfrowania linków YouTube (`brew install deno`).

## Uwagi

- Przy problemach z odtwarzaniem zaktualizuj yt-dlp: `pip install -U yt-dlp`.
- Linki do strumieni wygasają po pewnym czasie – wyszukaj/odtwórz ponownie.
- Używaj zgodnie z regulaminem YouTube i prawem w swoim kraju.
