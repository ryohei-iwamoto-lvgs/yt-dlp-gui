# yt-dlp-gui

A small cross-platform Tkinter GUI for [yt-dlp](https://github.com/yt-dlp/yt-dlp).
No third-party Python dependencies — only the standard library.

## Features

- URL input with clipboard paste
- Output directory picker (defaults to `~/Downloads`)
- Format presets: best / 1080p / 720p / 480p / mp3 / m4a
- Optional subtitles, thumbnail embedding, full-playlist download
- Live progress log with stop button
- "Open output folder" shortcut

## Requirements

- Python 3.10+ (uses `str | None` syntax) with Tkinter
- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) on `PATH`
- [`ffmpeg`](https://ffmpeg.org/) on `PATH` (required for merging video+audio, audio extraction, thumbnail embedding)

### Install (macOS)

```sh
brew install yt-dlp ffmpeg
```

### Install (other platforms)

See the [yt-dlp install guide](https://github.com/yt-dlp/yt-dlp#installation).

## Usage

```sh
python3 yt-dlp-gui.py
```

### macOS launcher

To launch by double-click, create a `.command` file on your Desktop:

```sh
cat > "$HOME/Desktop/yt-dlp GUI.command" <<'EOF'
#!/bin/bash
exec python3 "$HOME/path/to/yt-dlp-gui.py"
EOF
chmod +x "$HOME/Desktop/yt-dlp GUI.command"
```

## License

MIT
