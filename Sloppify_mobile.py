import tkinter as tk
import customtkinter as ctk
import yt_dlp
import pygame
import os
import requests
import random
from bs4 import BeautifulSoup
from threading import Thread
from PIL import Image, ImageTk, ImageSequence

# Audio Setup
pygame.mixer.init()

# --- STEP 1: STABLE ANIMATED GIF HANDLER ---
class AnimatedGIFLabel(ctk.CTkLabel):
    def __init__(self, master, gif_path, size=(140, 140), **kwargs):
        super().__init__(master, text="", **kwargs)
        self.cancel_id = None
        self.update_gif(gif_path, size)

    def update_gif(self, gif_path, size):
        if self.cancel_id:
            self.after_cancel(self.cancel_id)
            
        self.gif_path = gif_path
        self.size = size
        self.img = Image.open(gif_path)
        self.frames = []
        for frame in ImageSequence.Iterator(self.img):
            frame = frame.convert("RGBA").resize(self.size, Image.Resampling.LANCZOS)
            self.frames.append(ctk.CTkImage(light_image=frame, dark_image=frame, size=self.size))
        
        self.frame_index = 0
        self.animate()

    def animate(self):
        if not self.winfo_exists():
            return
            
        try:
            self.configure(image=self.frames[self.frame_index])
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            
            duration = self.img.info.get('duration', 100)
            if duration < 20: duration = 100 
            
            self.cancel_id = self.after(duration, self.animate)
        except Exception:
            pass 

# --- STEP 2: THE MAIN PLAYER ---
class SlopifyPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Slopify - Premium Sloppy Player")
        self.geometry("1000x700")
        ctk.set_appearance_mode("dark")
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.music_folder = os.path.join(self.base_dir, "downloads")
        if not os.path.exists(self.music_folder): os.makedirs(self.music_folder)

        self.playlist = []
        self.current_index = 0
        self.is_paused = False
        self.is_playing = False
        self.current_pos = 0 

        # --- Color Animation State ---
        self.red_value = 150  # Start at a medium red
        self.red_direction = 1 # 1 for getting brighter, -1 for darker

        # --- Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#000000", corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        # Interactive GIF Logo
        self.image_label = None
        self.change_gif()
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Slopify", 
                                      font=("UnifrakturCook", 36, "bold") if os.name == 'nt' else ("serif", 36, "bold"))
        self.logo_label.pack(pady=(10, 0))
        
        ctk.CTkLabel(self.sidebar, text="-", font=("Helvetica", 30, "bold")).pack()
        ctk.CTkLabel(self.sidebar, text="Song Downloader", font=("Helvetica", 18, "bold")).pack(pady=(0, 40))

        # Main View
        self.main_view = ctk.CTkFrame(self, fg_color="#121212", corner_radius=0)
        self.main_view.grid(row=0, column=1, sticky="nsew")

        self.url_entry = ctk.CTkEntry(self.main_view, placeholder_text="Paste Link or Song Name...", width=550, height=45)
        self.url_entry.pack(pady=(50, 10))
        
        self.download_btn = ctk.CTkButton(self.main_view, text="FETCH SONG", command=self.start_download_thread, 
                                          fg_color="#1DB954", text_color="black", hover_color="#17a34a")
        self.download_btn.pack()

        self.status_label = ctk.CTkLabel(self.main_view, text="Status: Ready", text_color="#777777")
        self.status_label.pack(pady=10)

        self.song_listbox = tk.Listbox(self.main_view, bg="#181818", fg="#b3b3b3", borderwidth=0, 
                                       font=("Helvetica", 12), highlightthickness=0, selectbackground="#282828")
        self.song_listbox.pack(fill="both", expand=True, padx=40, pady=20)
        self.song_listbox.bind("<Double-1>", lambda e: self.play_from_selection())

        # Control Bar
        self.controls = ctk.CTkFrame(self, height=150, fg_color="#181818", corner_radius=0)
        self.controls.grid(row=1, column=1, sticky="ew")
        self.ctrl_inner = ctk.CTkFrame(self.controls, fg_color="transparent")
        self.ctrl_inner.pack(expand=True)

        ctk.CTkButton(self.ctrl_inner, text="⏮", width=80, fg_color="#333333", command=self.prev_song).pack(side="left", padx=10)
        ctk.CTkButton(self.ctrl_inner, text="-10s", width=40, fg_color="#333333", command=lambda: self.seek(-10)).pack(side="left", padx=5)
        
        self.play_btn = ctk.CTkButton(self.ctrl_inner, text="▶", width=300, height=50, corner_radius=10, 
                                      fg_color="#333333", text_color="green", command=self.play_pause_toggle)
        self.play_btn.pack(side="left", padx=20)
        
        ctk.CTkButton(self.ctrl_inner, text="+10s", width=40, fg_color="#333333", command=lambda: self.seek(10)).pack(side="left", padx=5)
        ctk.CTkButton(self.ctrl_inner, text="⏭", width=80, fg_color="#333333", command=self.next_song).pack(side="left", padx=10)

        self.refresh_list()
        self.check_music_status()
        self.update_label_color() # Start the color shift

    # --- COLOR ANIMATION LOGIC ---
    def update_label_color(self):
        if not self.winfo_exists(): return
        
        # Shift the red value
        self.red_value += (5 * self.red_direction)
        
        # Reverse direction if we hit limits (Dark red 80 to Bright red 255)
        if self.red_value >= 255 or self.red_value <= 80:
            self.red_direction *= -1
        
        # Convert RGB to Hex string
        color_hex = f"#{self.red_value:02x}0000"
        self.logo_label.configure(text_color=color_hex)
        
        # Repeat every 50ms for a smooth fade
        self.after(50, self.update_label_color)

    # --- GIF LOGIC ---
    def change_gif(self, event=None):
        all_files = os.listdir(self.base_dir)
        gif_files = [f for f in all_files if f.lower().endswith('.gif')]
        
        if gif_files:
            chosen_gif = random.choice(gif_files)
            gif_path = os.path.join(self.base_dir, chosen_gif)
            
            if self.image_label is None:
                self.image_label = AnimatedGIFLabel(self.sidebar, gif_path, size=(160, 200))
                self.image_label.pack(pady=(40, 0))
                self.image_label.bind("<Button-1>", self.change_gif)
            else:
                self.image_label.update_gif(gif_path, size=(160, 200))

    # --- PLAYER LOGIC ---
    def seek(self, seconds):
        if not self.is_playing: return
        elapsed = (pygame.mixer.music.get_pos() / 1000.0)
        self.current_pos += elapsed + seconds
        if self.current_pos < 0: self.current_pos = 0
        path = os.path.join(self.music_folder, self.playlist[self.current_index])
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(start=self.current_pos)
        self.is_paused = False
        self.play_btn.configure(text="⏸")

    def check_music_status(self):
        if not self.winfo_exists(): return
        if self.is_playing and not pygame.mixer.music.get_busy() and not self.is_paused:
            self.next_song()
        self.after(1000, self.check_music_status)

    def refresh_list(self):
        self.song_listbox.delete(0, tk.END)
        fmts = ('.mp3', '.m4a', '.webm', '.opus')
        self.playlist = [f for f in os.listdir(self.music_folder) if f.lower().endswith(fmts)]
        for song in self.playlist: self.song_listbox.insert(tk.END, f"  {song}")

    def play_from_selection(self):
        s = self.song_listbox.curselection()
        if s: self.current_index = s[0]; self.play_song()

    def play_pause_toggle(self):
        if not self.playlist: return
        if pygame.mixer.music.get_busy() and not self.is_paused:
            self.current_pos += (pygame.mixer.music.get_pos() / 1000.0)
            pygame.mixer.music.pause(); self.is_paused = True; self.play_btn.configure(text="▶")
        elif self.is_paused:
            pygame.mixer.music.unpause(); self.is_paused = False; self.play_btn.configure(text="⏸")
        else: self.play_song()

    def play_song(self):
        if not self.playlist: return
        try:
            self.current_pos = 0
            path = os.path.join(self.music_folder, self.playlist[self.current_index])
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.is_paused = False; self.is_playing = True
            self.play_btn.configure(text="⏸")
            self.song_listbox.selection_clear(0, tk.END)
            self.song_listbox.selection_set(self.current_index)
            self.song_listbox.see(self.current_index)
        except: self.next_song()

    def next_song(self):
        if self.playlist: 
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_song()

    def prev_song(self):
        if self.playlist: 
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_song()

    # --- DOWNLOAD LOGIC ---
    def start_download_thread(self):
        val = self.url_entry.get()
        if val:
            self.status_label.configure(text="Status: Decoding...", text_color="#EAB308")
            Thread(target=self.download_logic, args=(val,), daemon=True).start()

    def download_logic(self, val):
        try:
            if "http" in val:
                r = requests.get(val, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                soup = BeautifulSoup(r.text, 'html.parser')
                search_text = soup.title.string.split('|')[0].replace('Spotify', '').strip()
            else: search_text = val
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.music_folder, '%(title)s.%(ext)s'),
                'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([f"ytsearch1:{search_text}"])
            self.after(0, lambda: self.status_label.configure(text="Status: Success!", text_color="#1DB954"))
        except:
            self.after(0, lambda: self.status_label.configure(text="Status: Failed", text_color="#EF4444"))
        finally:
            self.after(0, self.refresh_list)

if __name__ == "__main__":
    app = SlopifyPlayer()
    app.mainloop()
