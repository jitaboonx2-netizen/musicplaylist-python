import os
import random
import time
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pygame
import yt_dlp

# =========================
# Init
# =========================
pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(BASE_DIR, "playlist")
os.makedirs(MUSIC_DIR, exist_ok=True)

playlist = []
current_index = 0
paused = False
song_start_time = 0
song_length = 0

# =========================
# Playlist
# =========================
def load_playlist():
    global playlist
    playlist = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(".mp3")]
    playlist_box.delete(0, tk.END)
    for song in playlist:
        playlist_box.insert(tk.END, f"🎵 {song}")

# =========================
# Player
# =========================
def load_song(index):
    global current_index, paused, song_start_time, song_length
    if not playlist:
        messagebox.showinfo("ℹ️ แจ้งเตือน", "📭 ยังไม่มีเพลงใน Playlist")
        return

    current_index = index % len(playlist)
    path = os.path.join(MUSIC_DIR, playlist[current_index])

    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    pygame.mixer.music.set_volume(volume_slider.get())

    song_length = pygame.mixer.Sound(path).get_length()
    progress_slider.set(0)

    paused = False
    song_start_time = time.time()

    play_btn.configure(text="⏸")
    status_label.configure(
        text=f"🎶 กำลังเล่น: {playlist[current_index]}",
        text_color="#c084fc"
    )

    playlist_box.selection_clear(0, tk.END)
    playlist_box.selection_set(current_index)

def play_pause():
    global paused
    if pygame.mixer.music.get_busy():
        if paused:
            pygame.mixer.music.unpause()
            paused = False
            play_btn.configure(text="⏸")
            status_label.configure(text="▶️ เล่นต่อ", text_color="#a78bfa")
        else:
            pygame.mixer.music.pause()
            paused = True
            play_btn.configure(text="▶")
            status_label.configure(text="⏸ พักเพลง", text_color="#94a3b8")
    else:
        load_song(current_index)

def next_song(): load_song(current_index + 1)
def prev_song(): load_song(current_index - 1)

def shuffle_song():
    random.shuffle(playlist)
    load_playlist()
    load_song(0)
    status_label.configure(text="🔀 สุ่มเพลงแล้ว", text_color="#38bdf8")

def select_song(event):
    if playlist_box.curselection():
        load_song(playlist_box.curselection()[0])

# =========================
# Time
# =========================
def update_time():
    if pygame.mixer.music.get_busy() and not paused:
        elapsed = time.time() - song_start_time
        if song_length > 0:
            progress_slider.set(min(elapsed / song_length, 1))
        time_label.configure(
            text=f"⏱ {int(elapsed)//60:02}:{int(elapsed)%60:02}"
        )
    root.after(500, update_time)

def seek_song(val):
    global song_start_time
    if song_length > 0:
        pos = float(val) * song_length
        pygame.mixer.music.play(start=pos)
        song_start_time = time.time() - pos

# =========================
# Volume
# =========================
def set_volume(val):
    pygame.mixer.music.set_volume(float(val))

# =========================
# Add Local File
# =========================
def add_file():
    files = filedialog.askopenfilenames(
        title="📁 เลือกไฟล์เพลง",
        filetypes=[("MP3 files", "*.mp3")]
    )
    if not files:
        return

    for file in files:
        dest = os.path.join(MUSIC_DIR, os.path.basename(file))
        if not os.path.exists(dest):
            with open(file, "rb") as src, open(dest, "wb") as dst:
                dst.write(src.read())

    load_playlist()
    status_label.configure(text="✅ เพิ่มเพลงจากเครื่องแล้ว", text_color="#10b981")

# =========================
# Clipboard
# =========================
def paste_link():
    try:
        link = root.clipboard_get()
        yt_entry.delete(0, tk.END)
        yt_entry.insert(0, link)
        status_label.configure(text="📋 วางลิ้งแล้ว", text_color="#a78bfa")
    except:
        messagebox.showwarning("⚠️ เตือน", "ไม่มีลิ้งใน Clipboard")

# =========================
# YouTube → MP3
# =========================
def add_link():
    url = yt_entry.get().strip()
    if not url:
        messagebox.showwarning("⚠️ เตือน", "กรุณาวางลิ้ง YouTube")
        return

    status_label.configure(text="🚀 กำลังโหลดจาก YouTube...", text_color="#38bdf8")

    def task():
        try:
            ydl_opts = {
                "format": "bestaudio",
                "outtmpl": os.path.join(MUSIC_DIR, "%(title)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            yt_entry.delete(0, tk.END)
            load_playlist()
            status_label.configure(text="🎉 ดาวน์โหลดเสร็จแล้ว", text_color="#22c55e")
        except Exception as e:
            messagebox.showerror("❌ Error", str(e))

    threading.Thread(target=task, daemon=True).start()

# =========================
# UI – Galaxy Theme 🌌
# =========================
ctk.set_appearance_mode("dark")

root = ctk.CTk()
root.title("🌌 Galaxy Music Player")
root.geometry("480x700")
root.configure(fg_color="#0b0f1a")

# --- YouTube Section ---
link_frame = ctk.CTkFrame(root, fg_color="#161b33", corner_radius=15)
link_frame.pack(fill="x", padx=20, pady=15)

yt_entry = ctk.CTkEntry(
    link_frame,
    placeholder_text="📎 วางลิ้ง YouTube ที่นี่...",
    fg_color="#0b0f1a",
    border_color="#8b5cf6"
)
yt_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)

ctk.CTkButton(link_frame, text="📋 วาง", width=60, command=paste_link).pack(side="left", padx=5)
ctk.CTkButton(link_frame, text="⬇️ Add Link", width=90, command=add_link).pack(side="left", padx=5)

# --- Status ---
status_label = ctk.CTkLabel(
    root,
    text="✨ พร้อมใช้งาน",
    text_color="#c7d2fe",
    font=("Segoe UI", 13)
)
status_label.pack(pady=5)

# --- Add File / Shuffle ---
top_btns = ctk.CTkFrame(root, fg_color="transparent")
top_btns.pack(pady=5)

ctk.CTkButton(top_btns, text="📁 Add File", command=add_file).grid(row=0, column=0, padx=10)
ctk.CTkButton(top_btns, text="🔀 Shuffle", command=shuffle_song).grid(row=0, column=1, padx=10)

# --- Playlist ---
playlist_frame = ctk.CTkFrame(root, fg_color="#11162a")
playlist_frame.pack(fill="both", expand=True, padx=20, pady=10)

playlist_box = tk.Listbox(
    playlist_frame,
    bg="#0b0f1a",
    fg="#e0e7ff",
    selectbackground="#8b5cf6",
    font=("Segoe UI", 11),
    bd=0
)
playlist_box.pack(fill="both", expand=True, padx=10, pady=10)
playlist_box.bind("<<ListboxSelect>>", select_song)

# --- Controls ---
controls = ctk.CTkFrame(root, fg_color="transparent")
controls.pack(pady=10)

ctk.CTkButton(controls, text="⏮", width=55, command=prev_song).grid(row=0, column=0, padx=5)
play_btn = ctk.CTkButton(controls, text="▶", width=90, command=play_pause)
play_btn.grid(row=0, column=1, padx=5)
ctk.CTkButton(controls, text="⏭", width=55, command=next_song).grid(row=0, column=2, padx=5)

progress_slider = ctk.CTkSlider(root, from_=0, to=1, command=seek_song)
progress_slider.pack(fill="x", padx=40)

time_label = ctk.CTkLabel(root, text="⏱ 00:00", text_color="#94a3b8")
time_label.pack()

volume_slider = ctk.CTkSlider(root, from_=0, to=1, width=200, command=set_volume)
volume_slider.set(0.8)
volume_slider.pack(pady=10)

# =========================
# Start
# =========================
load_playlist()
update_time()
root.mainloop()
