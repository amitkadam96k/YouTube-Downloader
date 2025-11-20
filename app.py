import os
import threading
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import shutil
import subprocess
import traceback

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def ensure_output_dir(path):
    """Create directory if missing"""
    os.makedirs(path, exist_ok=True)
    return path


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    if shutil.which("ffmpeg") is None:
        messagebox.showwarning(
            "FFmpeg Missing",
            "⚠️ FFmpeg not found!\n\n"
            "Please install FFmpeg from:\nhttps://www.gyan.dev/ffmpeg/builds/\n"
            "Then add its 'bin' folder to your system PATH."
        )
        return False
    return True


def print_progress(d):
    """Update progress bar and label"""
    if d["status"] == "downloading":
        percent_str = (
            d.get("_percent_str", "")
            .replace("%", "")
            .replace("\x1b[0;94m", "")
            .replace("\x1b[0m", "")
            .strip()
        )
        try:
            percent = float(percent_str)
        except ValueError:
            percent = 0
        progress_bar["value"] = percent
        status_label.config(
            text=f"⬇️ {d.get('_percent_str','').strip()} | {d.get('_speed_str','')} | ETA: {d.get('_eta_str','')}"
        )
        root.update_idletasks()
    elif d["status"] == "finished":
        status_label.config(text="✅ Download complete! Finalizing...")


def download_video():
    """Triggered by Download button"""
    url = url_entry.get().strip()
    mode = mode_var.get()
    quality = quality_var.get()
    cookies_file = "cookies.txt"

    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL.")
        return

    if not check_ffmpeg():
        return

    # Output folders
    base_dir = ensure_output_dir(os.path.join(os.getcwd(), "downloads"))
    subfolder = "video" if mode == "video" else "audio"
    output_dir = ensure_output_dir(os.path.join(base_dir, subfolder))

    # Quality mapping
    quality_map = {
        "Best": "bestvideo+bestaudio/best",
        "2160p": "bestvideo[height=2160]+bestaudio/best",
        "1440p": "bestvideo[height=1440]+bestaudio/best",
        "1080p": "bestvideo[height=1080]+bestaudio/best",
        "720p": "bestvideo[height=720]+bestaudio/best",
        "480p": "bestvideo[height=480]+bestaudio/best",
        "360p": "bestvideo[height=360]+bestaudio/best",
    }
    video_format = quality_map.get(quality, "bestvideo+bestaudio/best")

    # yt-dlp options
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "progress_hooks": [print_progress],
        "quiet": True,
        "ignoreerrors": True,
        "noprogress": True,
        "color": "no_color",
        "merge_output_format": "mp4",
    }

    # Add cookies if available
    if os.path.exists(cookies_file):
        ydl_opts["cookiefile"] = cookies_file

    # Set audio or video mode
    if mode == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        ydl_opts.update({"format": video_format})

    def run_download():
        try:
            status_label.config(text="⏳ Downloading...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            status_label.config(text=f"✅ Done! Saved to: {output_dir}")
            open_folder_btn.config(state=NORMAL)
            play_vlc_btn.config(state=NORMAL)
        except yt_dlp.utils.DownloadError as e:
            msg = str(e)
            if "403" in msg:
                messagebox.showerror(
                    "403 Forbidden",
                    "🚫 YouTube blocked this download.\n"
                    "Try adding a 'cookies.txt' file for authentication."
                )
            elif "ffmpeg" in msg.lower():
                messagebox.showerror("FFmpeg Error", "⚠️ FFmpeg not found. Please install it and add to PATH.")
            else:
                messagebox.showerror("Download Error", f"❌ yt-dlp failed:\n{msg}")
            print("\n--- DOWNLOAD ERROR ---")
            traceback.print_exc()
            print("-----------------------\n")
            status_label.config(text="❌ Download failed.")
            open_folder_btn.config(state=DISABLED)
            play_vlc_btn.config(state=DISABLED)
        except Exception as e:
            print("\n--- UNKNOWN ERROR ---")
            traceback.print_exc()
            print("-----------------------\n")
            messagebox.showerror("Error", f"❌ Download failed:\n{e}")
            status_label.config(text="❌ Download failed.")
            open_folder_btn.config(state=DISABLED)
            play_vlc_btn.config(state=DISABLED)

    threading.Thread(target=run_download).start()


def open_download_folder():
    """Open the downloads directory"""
    base_dir = os.path.join(os.getcwd(), "downloads")
    try:
        os.startfile(base_dir)
    except Exception:
        subprocess.Popen(["xdg-open", base_dir])


def play_in_vlc():
    """Play latest video using VLC"""
    video_dir = os.path.join(os.getcwd(), "downloads", "video")
    if not os.path.exists(video_dir):
        messagebox.showinfo("VLC", "No video folder found yet.")
        return

    files = [f for f in os.listdir(video_dir) if f.endswith((".mp4", ".mkv", ".webm"))]
    if not files:
        messagebox.showinfo("VLC", "No video files found in downloads/video.")
        return

    latest = max([os.path.join(video_dir, f) for f in files], key=os.path.getctime)
    try:
        os.startfile(latest)
        status_label.config(text=f"▶️ Playing: {os.path.basename(latest)}")
    except Exception:
        try:
            subprocess.Popen(["vlc", latest])
            status_label.config(text=f"▶️ Playing with VLC: {os.path.basename(latest)}")
        except FileNotFoundError:
            messagebox.showwarning("VLC Missing", "⚠️ VLC not found. Please install VLC Media Player.")


def paste_url():
    """Paste YouTube URL from clipboard"""
    try:
        url_entry.delete(0, tk.END)
        url_entry.insert(0, root.clipboard_get())
        status_label.config(text="📋 URL pasted from clipboard!")
    except tk.TclError:
        messagebox.showwarning("Clipboard Empty", "⚠️ No text found in clipboard.")


def update_quality_state():
    """Enable/Disable quality dropdown based on mode"""
    if mode_var.get() == "audio":
        quality_dropdown.config(state="disabled")
        quality_label.config(state="disabled")
    else:
        quality_dropdown.config(state="readonly")
        quality_label.config(state="normal")


# ---------------------------------------------------------
# GUI Setup
# ---------------------------------------------------------

root = ttk.Window(themename="darkly")
root.title("🎬 YouTube Downloader by Amit")
root.geometry("620x480")
root.resizable(False, False)

# Title
ttk.Label(root, text="🎧 YouTube Downloader", font=("Segoe UI", 18, "bold")).pack(pady=10)

# URL Input + Paste Button
url_frame = ttk.Frame(root)
url_frame.pack(pady=5)

ttk.Label(url_frame, text="Enter YouTube URL:").pack(anchor="w", padx=2)

entry_frame = ttk.Frame(url_frame)
entry_frame.pack()

url_entry = ttk.Entry(entry_frame, width=55)
url_entry.pack(side="left", padx=5)

paste_btn = ttk.Button(entry_frame, text="📋 Paste", bootstyle=INFO, command=paste_url)
paste_btn.pack(side="left", padx=5)

# Mode selection
mode_var = tk.StringVar(value="audio")
mode_frame = ttk.Frame(root)
mode_frame.pack(pady=5)
ttk.Label(mode_frame, text="Download Mode:").pack(side="left", padx=5)
ttk.Radiobutton(mode_frame, text="Audio (MP3)", variable=mode_var, value="audio", command=update_quality_state).pack(side="left", padx=10)
ttk.Radiobutton(mode_frame, text="Video (MP4)", variable=mode_var, value="video", command=update_quality_state).pack(side="left", padx=10)

# Quality dropdown
quality_var = tk.StringVar(value="Best")
quality_label = ttk.Label(root, text="Select Quality:")
quality_label.pack(pady=(10, 0))
quality_dropdown = ttk.Combobox(root, textvariable=quality_var, state="disabled", width=20)
quality_dropdown["values"] = ["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
quality_dropdown.pack(pady=5)

# Progress bar
progress_bar = ttk.Progressbar(root, length=520, mode="determinate")
progress_bar.pack(pady=20)

# Status label
status_label = ttk.Label(root, text="Ready.", font=("Segoe UI", 10))
status_label.pack()

# Buttons
btn_frame = ttk.Frame(root)
btn_frame.pack(pady=10)
download_btn = ttk.Button(btn_frame, text="⬇️ Download", bootstyle=SUCCESS, command=download_video)
download_btn.pack(side="left", padx=10)
open_folder_btn = ttk.Button(btn_frame, text="📂 Open Folder", bootstyle=INFO, command=open_download_folder, state=DISABLED)
open_folder_btn.pack(side="left", padx=10)
play_vlc_btn = ttk.Button(btn_frame, text="▶️ Play in VLC", bootstyle=SECONDARY, command=play_in_vlc, state=DISABLED)
play_vlc_btn.pack(side="left", padx=10)

# ---------------------------------------------------------
# Run GUI
# ---------------------------------------------------------
root.mainloop()
