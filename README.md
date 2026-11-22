# YT Bez Reklam

Kompaktowa aplikacja webowa (Flask + yt-dlp): wyszukuje filmy w YouTube i odtwarza je w przeglądarce bez reklam, z pełnym przewijaniem. Cały kod to jeden plik `app.py`.

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

## Tryby odtwarzania

- **Odtwórz (domyślnie)** – film jest pobierany do katalogu `downloads/` (najlepsza dostępna jakość do 1080p), a potem odtwarzany z pliku. Daje pełne przewijanie paskiem. Przy pierwszym odtworzeniu trzeba poczekać na pobranie (pokazuje się postęp), kolejne starty są natychmiastowe.
- **Strumień** – odtwarzanie na żywo bez pobierania (yt-dlp → ffmpeg). Start jest szybszy, ale przewijanie jest ograniczone.

Pliki w `downloads/` zostają na dysku; usuń je ręcznie, gdy nie są potrzebne (`rm -rf downloads/`).

## Uwagi

- Przy problemach z odtwarzaniem zaktualizuj yt-dlp: `pip install -U yt-dlp`.
- Aplikacja jest przeznaczona do użytku lokalnego (nasłuchuje na 127.0.0.1).
- Używaj zgodnie z regulaminem YouTube i prawem w swoim kraju.
