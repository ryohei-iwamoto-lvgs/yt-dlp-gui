#!/usr/bin/env python3
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

DEFAULT_DIR = str(Path.home() / "Downloads")

FORMAT_PRESETS = {
    "ベスト画質 (動画+音声)": [
        "-f",
        "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b",
    ],
    "1080p 以下": [
        "-f",
        "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b[height<=1080]",
    ],
    "720p 以下": [
        "-f",
        "bv*[height<=720][ext=mp4]+ba[ext=m4a]/bv*[height<=720]+ba/b[height<=720]",
    ],
    "480p 以下": [
        "-f",
        "bv*[height<=480][ext=mp4]+ba[ext=m4a]/bv*[height<=480]+ba/b[height<=480]",
    ],
    "音声のみ (mp3)": ["-x", "--audio-format", "mp3", "--audio-quality", "0"],
    "音声のみ (m4a)": ["-x", "--audio-format", "m4a", "--audio-quality", "0"],
}

VIDEO_PRESET_NAMES = {
    "ベスト画質 (動画+音声)",
    "1080p 以下",
    "720p 以下",
    "480p 以下",
}


def find_yt_dlp() -> str | None:
    return shutil.which("yt-dlp")


class YtDlpGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("yt-dlp GUI")
        self.geometry("760x560")
        self.minsize(640, 480)

        self.proc: subprocess.Popen | None = None
        self.log_queue: queue.Queue[str] = queue.Queue()

        self._build_ui()
        self.after(100, self._drain_log_queue)

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # URL
        url_frame = ttk.Frame(self)
        url_frame.pack(fill="x", **pad)
        ttk.Label(url_frame, text="URL:").pack(side="left")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(8, 8))
        ttk.Button(url_frame, text="貼り付け", command=self._paste).pack(side="left")

        # Output dir
        dir_frame = ttk.Frame(self)
        dir_frame.pack(fill="x", **pad)
        ttk.Label(dir_frame, text="保存先:").pack(side="left")
        self.dir_var = tk.StringVar(value=DEFAULT_DIR)
        ttk.Entry(dir_frame, textvariable=self.dir_var).pack(
            side="left", fill="x", expand=True, padx=(8, 8)
        )
        ttk.Button(dir_frame, text="選択...", command=self._choose_dir).pack(side="left")

        # Format / options
        opt_frame = ttk.Frame(self)
        opt_frame.pack(fill="x", **pad)
        ttk.Label(opt_frame, text="フォーマット:").pack(side="left")
        self.format_var = tk.StringVar(value=next(iter(FORMAT_PRESETS)))
        ttk.Combobox(
            opt_frame,
            textvariable=self.format_var,
            values=list(FORMAT_PRESETS.keys()),
            state="readonly",
            width=28,
        ).pack(side="left", padx=(8, 16))

        self.subs_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="字幕も保存", variable=self.subs_var).pack(side="left")
        self.thumb_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="サムネイル埋め込み", variable=self.thumb_var).pack(
            side="left", padx=(12, 0)
        )
        self.playlist_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="プレイリスト全件", variable=self.playlist_var).pack(
            side="left", padx=(12, 0)
        )

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", **pad)
        self.dl_btn = ttk.Button(btn_frame, text="ダウンロード開始", command=self._start)
        self.dl_btn.pack(side="left")
        self.stop_btn = ttk.Button(
            btn_frame, text="停止", command=self._stop, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(8, 0))
        ttk.Button(btn_frame, text="保存先を開く", command=self._open_dir).pack(side="left", padx=(8, 0))
        ttk.Button(btn_frame, text="ログをクリア", command=self._clear_log).pack(
            side="right"
        )

        # Status
        self.status_var = tk.StringVar(value="待機中")
        ttk.Label(self, textvariable=self.status_var, anchor="w").pack(
            fill="x", padx=10
        )

        # Log
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.log = scrolledtext.ScrolledText(log_frame, wrap="word", height=18)
        self.log.pack(fill="both", expand=True)
        self.log.configure(state="disabled")

    def _paste(self):
        try:
            self.url_var.set(self.clipboard_get())
        except tk.TclError:
            pass

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get() or DEFAULT_DIR)
        if d:
            self.dir_var.set(d)

    def _open_dir(self):
        d = self.dir_var.get()
        if d and Path(d).is_dir():
            subprocess.Popen(["open", d])

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _append_log(self, text: str):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _drain_log_queue(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                self._append_log(line)
                stripped = line.strip()
                if stripped:
                    # Update status with last meaningful line
                    self.status_var.set(stripped[:200])
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _build_command(self, url: str) -> list[str]:
        yt_dlp = find_yt_dlp()
        if not yt_dlp:
            raise RuntimeError("yt-dlp が見つかりません。`brew install yt-dlp` などで導入してください。")

        out_dir = self.dir_var.get() or DEFAULT_DIR
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        cmd: list[str] = [
            yt_dlp,
            "--newline",
            "--progress",
            "-o",
            os.path.join(out_dir, "%(title)s [%(id)s].%(ext)s"),
        ]
        preset = self.format_var.get()
        cmd += FORMAT_PRESETS[preset]

        if preset in VIDEO_PRESET_NAMES:
            cmd += [
                "--merge-output-format", "mp4",
                "--remux-video", "mp4",
            ]

        if self.subs_var.get():
            cmd += ["--write-subs", "--write-auto-subs", "--sub-langs", "ja,en"]
        if self.thumb_var.get():
            cmd += ["--embed-thumbnail", "--add-metadata"]
        if not self.playlist_var.get():
            cmd += ["--no-playlist"]

        cmd.append(url)
        return cmd

    def _start(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL 未入力", "ダウンロードする URL を入力してください。")
            return
        if self.proc and self.proc.poll() is None:
            return

        try:
            cmd = self._build_command(url)
        except Exception as e:
            messagebox.showerror("エラー", str(e))
            return

        self._append_log("$ " + " ".join(cmd) + "\n")
        self.dl_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set("開始中...")

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
            )
        except Exception as e:
            messagebox.showerror("起動失敗", str(e))
            self._reset_buttons()
            return

        threading.Thread(target=self._reader_thread, daemon=True).start()

    def _reader_thread(self):
        assert self.proc is not None
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.log_queue.put(line)
        rc = self.proc.wait()
        self.log_queue.put(f"\n[終了コード: {rc}]\n")
        self.after(0, self._reset_buttons)

    def _reset_buttons(self):
        self.dl_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        if self.proc and self.proc.returncode == 0:
            self.status_var.set("完了")
        elif self.proc:
            self.status_var.set(f"終了 (code={self.proc.returncode})")

    def _stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.status_var.set("停止中...")


if __name__ == "__main__":
    if sys.platform == "darwin":
        try:
            from tkinter import font as tkfont
            tkfont.nametofont("TkDefaultFont").configure(size=12)
        except Exception:
            pass
    YtDlpGUI().mainloop()
