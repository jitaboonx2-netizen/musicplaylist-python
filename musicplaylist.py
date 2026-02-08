import os
import random
import time
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import pygame

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
# Functions
# =========================
def load_playlist():
    global playlist
    playlist = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(".mp3")]
    playlist_box.delete(0, tk.END)
    for song in playlist:
        playlist_box.insert(tk.END, song)

def load_song(index):
    global current_index, paused, song_start_time, song_length
    if not playlist:
        status_label.configure(text="❌ ไม่มีเพลง", text_color="red")
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

    play_btn.configure(text="⏸ Pause")
    status_label.configure(text=f"▶ {playlist[current_index]}", text_color="#c084fc")

    playlist_box.selection_clear(0, tk.END)
    playlist_box.selection_set(current_index)

def play_pause():
    global paused
    if pygame.mixer.music.get_busy():
        if paused:
            pygame.mixer.music.unpause()
            paused = False
            play_btn.configure(text="⏸ Pause")
        else:
            pygame.mixer.music.pause()
            paused = True
            play_btn.configure(text="▶ Resume")
    else:
        load_song(current_index)

def stop_song():
    pygame.mixer.music.stop()
    play_btn.configure(text="▶ Play")
    status_label.configure(text="⏹ หยุดเพลง", text_color="gray")
    progress_slider.set(0)

def next_song():
    load_song(current_index + 1)

def prev_song():
    load_song(current_index - 1)

def shuffle_song():
    global playlist, current_index
    random.shuffle(playlist)
    current_index = 0
    load_playlist()
    load_song(current_index)

def select_song(event):
    if playlist_box.curselection():
        load_song(playlist_box.curselection()[0])

def set_volume(val):
    pygame.mixer.music.set_volume(float(val))

def volume_up():
    v = min(volume_slider.get() + 0.1, 1.0)
    volume_slider.set(v)
    pygame.mixer.music.set_volume(v)

def volume_down():
    v = max(volume_slider.get() - 0.1, 0.0)
    volume_slider.set(v)
    pygame.mixer.music.set_volume(v)

def add_songs():
    files = filedialog.askopenfilenames(
        title="เลือกไฟล์เพลง",
        filetypes=[("MP3 files", "*.mp3")]
    )
    for file in files:
        name = os.path.basename(file)
        dest = os.path.join(MUSIC_DIR, name)
        if not os.path.exists(dest):
            with open(file, "rb") as src, open(dest, "wb") as dst:
                dst.write(src.read())
    load_playlist()

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

def auto_next():
    if not pygame.mixer.music.get_busy() and not paused:
        next_song()
    root.after(1500, auto_next)

# =========================
# GUI
# =========================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("musicplaylist 🎧")
root.geometry("420x420")

status_label = ctk.CTkLabel(root, text="🎵 เลือกเพลงแล้วกด Play", font=("Arial", 14))
status_label.pack(pady=10)

playlist_frame = ctk.CTkFrame(root)
playlist_frame.pack(fill="both", expand=True, padx=15)

playlist_box = tk.Listbox(
    playlist_frame,
    bg="#1f1b24",
    fg="white",
    selectbackground="#7c3aed",
    font=("Arial", 12),
    relief="flat",
    bd=0
)
playlist_box.pack(side="left", fill="both", expand=True)
playlist_box.bind("<<ListboxSelect>>", select_song)

scroll = tk.Scrollbar(playlist_frame, command=playlist_box.yview)
scroll.pack(side="right", fill="y")
playlist_box.config(yscrollcommand=scroll.set)

controls = ctk.CTkFrame(root, fg_color="transparent")
controls.pack(pady=10)

ctk.CTkButton(controls, text="⏮", width=60, command=prev_song).grid(row=0, column=0, padx=5)
play_btn = ctk.CTkButton(controls, text="▶ Play", width=120, command=play_pause)
play_btn.grid(row=0, column=1, padx=5)
ctk.CTkButton(controls, text="⏹", width=60, command=stop_song).grid(row=0, column=2, padx=5)
ctk.CTkButton(controls, text="⏭", width=60, command=next_song).grid(row=0, column=3, padx=5)

progress_slider = ctk.CTkSlider(root, from_=0, to=1, command=seek_song)
progress_slider.pack(fill="x", padx=20, pady=5)

ctk.CTkButton(root, text="➕ เพิ่มเพลง", command=add_songs).pack(pady=3)
ctk.CTkButton(root, text="🔀 Shuffle", command=shuffle_song).pack(pady=3)

# ===== Volume Control =====
volume_frame = ctk.CTkFrame(root, fg_color="transparent")
volume_frame.pack(pady=8)

ctk.CTkButton(volume_frame, text="🔉 −", width=50, command=volume_down).grid(row=0, column=0, padx=5)

volume_slider = ctk.CTkSlider(
    volume_frame,
    from_=0,
    to=1,
    number_of_steps=20,
    command=set_volume,
    width=180
)
volume_slider.set(0.8)
volume_slider.grid(row=0, column=1)

ctk.CTkButton(volume_frame, text="🔊 +", width=50, command=volume_up).grid(row=0, column=2, padx=5)

time_label = ctk.CTkLabel(root, text="⏱ 00:00", text_color="gray")
time_label.pack()

# =========================
# Start
# =========================
load_playlist()
update_time()
auto_next()
root.mainloop()
