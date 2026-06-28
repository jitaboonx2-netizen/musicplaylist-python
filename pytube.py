import os
import random
import webbrowser
import json
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pygame

# =============================================================
# CONFIG
# =============================================================
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR    = os.path.join(BASE_DIR, "playlist")
CONFIG_FILE  = os.path.join(BASE_DIR, "config.json")
os.makedirs(MUSIC_DIR, exist_ok=True)

# =============================================================
# STATE
# =============================================================
playlist       = []       # [{"type": "mp3"|"yt", "value": str, "label": str}]
current_index  = -1
paused         = False
song_length    = 0
seeking        = False
shuffle_mode   = False
repeat_mode    = False
dark_mode      = True

# =============================================================
# COLORS
# =============================================================
C_BG     = "#0f0f1a"
C_PANEL  = "#1a1a2e"
C_BLUE   = "#3b82f6"
C_BLUE_H = "#2563eb"
C_PINK   = "#ec4899"
C_PINK_H = "#db2777"
C_TEXT   = "#f0f0ff"
C_SUB    = "#a0a0c0"

# =============================================================
# CONFIG LOAD/SAVE
# =============================================================
def load_config():
    global dark_mode, shuffle_mode, repeat_mode, current_index
    if not os.path.exists(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)

        # Dark mode — ใช้เปลี่ยนธีมจริง
        dark_mode = cfg.get("dark_mode", True)
        ctk.set_appearance_mode("dark" if dark_mode else "light")
        theme_btn.configure(text="🌙" if dark_mode else "☀️")

        # Volume
        vol = cfg.get("volume", 0.8)
        volume_slider.set(vol)
        pygame.mixer.music.set_volume(vol)
        vol_label.configure(text=f"🔊 {int(vol * 100)}%")

        # Shuffle / Repeat (sync UI โดยไม่สลับค่า)
        shuffle_mode = cfg.get("shuffle_mode", False)
        repeat_mode  = cfg.get("repeat_mode", False)
        _sync_shuffle_ui()
        _sync_repeat_ui()

        # เพลงล่าสุด
        idx = cfg.get("last_song_index", 0)
        if playlist and 0 <= idx < len(playlist):
            current_index = idx
            _highlight_current()
            _update_song_label(playlist[idx]["label"])
            _update_status(f"📌 เพลงล่าสุด: {playlist[idx]['label']}")

        # Window size
        size = cfg.get("window_size", "500x760")
        root.geometry(size)

    except Exception as e:
        print("⚠️ โหลด config ผิดพลาด:", e)


def save_config():
    try:
        cfg = {
            "dark_mode":       dark_mode,
            "volume":          round(volume_slider.get(), 2),
            "shuffle_mode":    shuffle_mode,
            "repeat_mode":     repeat_mode,
            "last_song_index": current_index,
            "window_size":     root.geometry(),
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠️ บันทึก config ผิดพลาด:", e)

# =============================================================
# PLAYLIST
# =============================================================
def load_playlist():
    playlist.clear()
    playlist_box.delete(0, tk.END)
    for f in sorted(os.listdir(MUSIC_DIR)):
        if f.lower().endswith(".mp3"):
            label = os.path.splitext(f)[0]
            playlist.append({"type": "mp3", "value": f, "label": label})
            playlist_box.insert(tk.END, f"  🎵  {label}")
    _update_status(f"โหลดแล้ว {len(playlist)} เพลง")


def _update_status(msg):
    status_label.configure(text=msg)


def _highlight_current():
    playlist_box.selection_clear(0, tk.END)
    if 0 <= current_index < playlist_box.size():
        playlist_box.selection_set(current_index)
        playlist_box.see(current_index)

# =============================================================
# PLAYER CORE
# =============================================================
def load_song(index, force_play=True):
    global current_index, paused, song_length

    if not playlist or not (0 <= index < len(playlist)):
        return

    item = playlist[index]
    current_index = index

    if item["type"] == "yt":
        webbrowser.open(item["value"])
        _update_status(f"🌐 เปิด YouTube: {item['label']}")
        _highlight_current()
        return

    path = os.path.join(MUSIC_DIR, item["value"])
    if not os.path.exists(path):
        messagebox.showerror("ไม่พบไฟล์", f"ไม่พบ: {item['value']}")
        return

    try:
        pygame.mixer.music.load(path)
        if force_play:
            pygame.mixer.music.play()
            pygame.mixer.music.set_volume(volume_slider.get())
            song_length = pygame.mixer.Sound(path).get_length()
            paused = False
            play_btn.configure(text="⏸")
        _update_status(f"🎶  {item['label']}")
        _highlight_current()
        _update_song_label(item["label"])
    except Exception as e:
        messagebox.showerror("เกิดข้อผิดพลาด", str(e))


def _update_song_label(name):
    max_len = 38
    display = name if len(name) <= max_len else name[:max_len] + "…"
    song_name_label.configure(text=display)


def play_pause(event=None):
    global paused
    if not playlist:
        return
    if current_index < 0:
        load_song(0)
        return

    if paused:
        pygame.mixer.music.unpause()
        paused = False
        play_btn.configure(text="⏸")
    elif pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        paused = True
        play_btn.configure(text="▶")
    else:
        load_song(current_index)


def next_song(event=None):
    if not playlist:
        return
    if shuffle_mode:
        idx = random.randint(0, len(playlist) - 1)
    else:
        idx = (current_index + 1) % len(playlist)
    load_song(idx)


def prev_song(event=None):
    if not playlist:
        return
    idx = (current_index - 1) % len(playlist)
    load_song(idx)


def select_song(event=None):
    sel = playlist_box.curselection()
    if sel:
        load_song(sel[0])


def stop_song(event=None):
    global paused
    pygame.mixer.music.stop()
    paused = False
    play_btn.configure(text="▶")
    progress_slider.set(0)
    time_label.configure(text="00:00 / 00:00")
    _update_status("⏹  หยุดแล้ว")

# =============================================================
# SHUFFLE / REPEAT
# =============================================================
def toggle_shuffle():
    global shuffle_mode
    shuffle_mode = not shuffle_mode
    _sync_shuffle_ui()
    save_config()


def _sync_shuffle_ui():
    shuffle_btn.configure(
        fg_color=C_BLUE if shuffle_mode else "transparent",
        text_color="white" if shuffle_mode else C_BLUE
    )


def toggle_repeat():
    global repeat_mode
    repeat_mode = not repeat_mode
    _sync_repeat_ui()
    save_config()


def _sync_repeat_ui():
    repeat_btn.configure(
        fg_color=C_PINK if repeat_mode else "transparent",
        text_color="white" if repeat_mode else C_PINK
    )

# =============================================================
# DARK MODE
# =============================================================
def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    ctk.set_appearance_mode("dark" if dark_mode else "light")
    theme_btn.configure(text="🌙" if dark_mode else "☀️")
    save_config()

# =============================================================
# TIME & SEEK
# =============================================================
def _fmt(sec):
    sec = max(0, int(sec))
    return f"{sec // 60:02}:{sec % 60:02}"


def update_time():
    if pygame.mixer.music.get_busy() and not paused and not seeking:
        elapsed = pygame.mixer.music.get_pos() / 1000.0
        if song_length > 0:
            progress_slider.set(min(elapsed / song_length, 1.0))
            time_label.configure(text=f"{_fmt(elapsed)} / {_fmt(song_length)}")
    elif not pygame.mixer.music.get_busy() and not paused and current_index >= 0:
        if repeat_mode:
            load_song(current_index)
        else:
            next_song()
    root.after(400, update_time)


def seek_start(event):
    global seeking
    seeking = True


def seek_song(val):
    if song_length > 0:
        pos = float(val) * song_length
        pygame.mixer.music.play(start=pos)
        pygame.mixer.music.set_volume(volume_slider.get())


def seek_end(event):
    global seeking
    seeking = False

# =============================================================
# VOLUME
# =============================================================
def set_volume(val):
    pygame.mixer.music.set_volume(float(val))
    vol_pct = int(float(val) * 100)
    vol_label.configure(text=f"🔊 {vol_pct}%")

# =============================================================
# ADD / REMOVE FILES
# =============================================================
def add_file():
    files = filedialog.askopenfilenames(
        title="เลือกไฟล์ MP3",
        filetypes=[("MP3 Files", "*.mp3"), ("All Files", "*.*")]
    )
    added = 0
    for f in files:
        dest = os.path.join(MUSIC_DIR, os.path.basename(f))
        if not os.path.exists(dest):
            try:
                with open(f, "rb") as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                added += 1
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", str(e))
    load_playlist()
    if added:
        messagebox.showinfo("สำเร็จ", f"เพิ่ม {added} เพลงแล้ว 🎶")


def add_youtube():
    url = yt_entry.get().strip()
    if not url.startswith("http"):
        messagebox.showwarning("ลิงก์ไม่ถูกต้อง", "กรุณาวางลิงก์ YouTube ที่ถูกต้อง")
        return
    label = url.split("v=")[-1][:11] if "v=" in url else url[-20:]
    playlist.append({"type": "yt", "value": url, "label": f"YouTube: {label}"})
    playlist_box.insert(tk.END, f"  ▶️  YouTube: {label}")
    yt_entry.delete(0, tk.END)
    _update_status("📌 เพิ่ม YouTube แล้ว")


def paste_youtube():
    try:
        yt_entry.delete(0, tk.END)
        yt_entry.insert(0, root.clipboard_get())
    except Exception:
        messagebox.showwarning("เตือน", "ไม่มีลิงก์ใน Clipboard")


def remove_song():
    sel = playlist_box.curselection()
    if not sel:
        return
    idx = sel[0]
    item = playlist[idx]
    if item["type"] == "mp3":
        if messagebox.askyesno("ลบเพลง", f"ลบ '{item['label']}' ออกจากโฟลเดอร์ด้วยหรือเปล่า?"):
            try:
                os.remove(os.path.join(MUSIC_DIR, item["value"]))
            except Exception:
                pass
    playlist.pop(idx)
    playlist_box.delete(idx)
    _update_status(f"ลบแล้ว: {item['label']}")

# =============================================================
# UI BUILD
# =============================================================
pygame.mixer.init()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
root = ctk.CTk()
root.title("🎧 Music Player")
root.geometry("500x760")
root.resizable(False, False)
root.configure(fg_color=C_BG)

# ----- Header -----
header = ctk.CTkFrame(root, fg_color="transparent")
header.pack(fill="x", padx=20, pady=(16, 0))
ctk.CTkLabel(
    header, text="🎧 Music Player",
    font=ctk.CTkFont("Segoe UI", 24, "bold"),
    text_color=C_PINK
).pack(side="left")
theme_btn = ctk.CTkButton(
    header, text="🌙", width=40, height=32,
    fg_color="transparent",
    border_width=1, border_color=C_PINK,
    text_color=C_PINK,
    command=toggle_dark_mode
)
theme_btn.pack(side="right")

# ----- Now Playing -----
now_frame = ctk.CTkFrame(root, corner_radius=14, fg_color=C_PANEL)
now_frame.pack(fill="x", padx=20, pady=(12, 6))
song_name_label = ctk.CTkLabel(
    now_frame, text="— ยังไม่ได้เลือกเพลง —",
    font=ctk.CTkFont("Segoe UI", 13, "bold"),
    text_color=C_TEXT, wraplength=440
)
song_name_label.pack(pady=(12, 4))
status_label = ctk.CTkLabel(
    now_frame, text="พร้อมใช้งาน",
    font=ctk.CTkFont("Segoe UI", 11),
    text_color=C_SUB
)
status_label.pack(pady=(0, 10))

# ----- Progress -----
prog_frame = ctk.CTkFrame(root, fg_color="transparent")
prog_frame.pack(fill="x", padx=20)
progress_slider = ctk.CTkSlider(
    prog_frame, from_=0, to=1, command=seek_song,
    button_color=C_PINK, button_hover_color=C_PINK_H,
    progress_color=C_PINK, fg_color="#2a2a3e"
)
progress_slider.set(0)
progress_slider.pack(fill="x")
progress_slider.bind("<ButtonPress-1>", seek_start)
progress_slider.bind("<ButtonRelease-1>", seek_end)
time_label = ctk.CTkLabel(
    prog_frame, text="00:00 / 00:00",
    font=ctk.CTkFont("Segoe UI", 10),
    text_color=C_SUB
)
time_label.pack(anchor="e")

# ----- Controls -----
ctrl = ctk.CTkFrame(root, fg_color="transparent")
ctrl.pack(pady=8)
shuffle_btn = ctk.CTkButton(
    ctrl, text="⇄", width=44, height=38,
    fg_color="transparent", border_width=1,
    border_color=C_BLUE, text_color=C_BLUE,
    hover_color="#1e3a5f",
    command=toggle_shuffle
)
shuffle_btn.grid(row=0, column=0, padx=4)
ctk.CTkButton(
    ctrl, text="⏮", width=52, height=38,
    fg_color=C_BLUE, hover_color=C_BLUE_H,
    command=prev_song
).grid(row=0, column=1, padx=4)
play_btn = ctk.CTkButton(
    ctrl, text="▶", width=72, height=48,
    font=ctk.CTkFont(size=20),
    fg_color=C_PINK, hover_color=C_PINK_H,
    command=play_pause
)
play_btn.grid(row=0, column=2, padx=4)
ctk.CTkButton(
    ctrl, text="⏭", width=52, height=38,
    fg_color=C_BLUE, hover_color=C_BLUE_H,
    command=next_song
).grid(row=0, column=3, padx=4)
ctk.CTkButton(
    ctrl, text="⏹", width=44, height=38,
    fg_color="transparent", border_width=1,
    border_color=C_BLUE, text_color=C_BLUE,
    hover_color="#1e3a5f",
    command=stop_song
).grid(row=0, column=4, padx=4)
repeat_btn = ctk.CTkButton(
    ctrl, text="↻", width=44, height=38,
    fg_color="transparent", border_width=1,
    border_color=C_PINK, text_color=C_PINK,
    hover_color="#3d1a2e",
    command=toggle_repeat
)
repeat_btn.grid(row=0, column=5, padx=4)

# ----- Volume -----
vol_frame = ctk.CTkFrame(root, fg_color="transparent")
vol_frame.pack(fill="x", padx=20, pady=(4, 0))
vol_label = ctk.CTkLabel(vol_frame, text="🔊 80%", width=60, text_color=C_SUB)
vol_label.pack(side="left")
volume_slider = ctk.CTkSlider(
    vol_frame, from_=0, to=1, command=set_volume,
    button_color=C_BLUE, button_hover_color=C_BLUE_H,
    progress_color=C_BLUE, fg_color="#2a2a3e"
)
volume_slider.set(0.8)
volume_slider.pack(side="left", fill="x", expand=True, padx=8)

# ----- Playlist -----
list_frame = ctk.CTkFrame(root, corner_radius=14, fg_color=C_PANEL)
list_frame.pack(fill="both", expand=True, padx=20, pady=10)
ctk.CTkLabel(
    list_frame, text="PLAYLIST",
    font=ctk.CTkFont("Segoe UI", 10, "bold"),
    text_color=C_BLUE
).pack(anchor="w", padx=12, pady=(8, 2))
playlist_box = tk.Listbox(
    list_frame,
    font=("Segoe UI", 11),
    bg=C_PANEL, fg=C_TEXT,
    selectbackground=C_PINK,
    selectforeground="white",
    activestyle="none",
    borderwidth=0, highlightthickness=0,
    relief="flat"
)
playlist_box.pack(fill="both", expand=True, padx=6, pady=(0, 6))
playlist_box.bind("<<ListboxSelect>>", select_song)

# ----- Add / Remove -----
action_frame = ctk.CTkFrame(root, fg_color="transparent")
action_frame.pack(fill="x", padx=20, pady=(0, 6))
ctk.CTkButton(
    action_frame, text="📂 เพิ่ม MP3", width=130,
    fg_color=C_BLUE, hover_color=C_BLUE_H,
    command=add_file
).pack(side="left", padx=(0, 6))
ctk.CTkButton(
    action_frame, text="🗑 ลบเพลง", width=110,
    fg_color=C_PINK, hover_color=C_PINK_H,
    command=remove_song
).pack(side="left")

# ----- YouTube -----
yt_frame = ctk.CTkFrame(root, fg_color="transparent")
yt_frame.pack(fill="x", padx=20, pady=(0, 14))
yt_entry = ctk.CTkEntry(
    yt_frame, placeholder_text="วางลิงก์ YouTube…",
    fg_color=C_PANEL, border_color=C_BLUE
)
yt_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
ctk.CTkButton(
    yt_frame, text="📋", width=38,
    fg_color=C_BLUE, hover_color=C_BLUE_H,
    command=paste_youtube
).pack(side="left", padx=(0, 4))
ctk.CTkButton(
    yt_frame, text="➕", width=38,
    fg_color=C_PINK, hover_color=C_PINK_H,
    command=add_youtube
).pack(side="left")

# =============================================================
# Keyboard shortcuts
# =============================================================
root.bind("<space>", play_pause)
root.bind("<Right>", next_song)
root.bind("<Left>", prev_song)
root.bind("s", lambda e: toggle_shuffle())
root.bind("r", lambda e: toggle_repeat())

# =============================================================
# START
# =============================================================
load_playlist()
load_config()
update_time()
root.protocol("WM_DELETE_WINDOW", lambda: (save_config(), root.destroy()))
root.mainloop()
pygame.mixer.quit()