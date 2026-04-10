import streamlit as st
import os
import random
import yt_dlp
import time
from pathlib import Path

# --- PAGE CONFIG ---
# Setting the favicon to a banana as a nod to the "sloppy" vibe
st.set_page_config(page_title="Slopify Mobile", page_icon="🍌", layout="wide")

# --- STEP 1: MATCHING THE DESKTOP VIBE (CSS) ---
st.markdown("""
    <style>
    /* Import the font from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=UnifrakturCook:wght@700&display=swap');

    /* Pulsing Red Logo */
    @keyframes pulse {
        0% { color: #550000; }
        50% { color: #ff0000; }
        100% { color: #550000; }
    }
    
    .slopify-logo {
        /* Use the imported font first, fallback to serif */
        font-family: 'UnifrakturCook', serif;
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        animation: pulse 3s infinite;
        margin-bottom: 0px;
    }
    
    .sub-text {
        color: #777777;
        text-align: center;
        font-size: 14px;
        margin-top: -10px;
        margin-bottom: 20px;
    }

    .stApp { background-color: #121212; }
    [data-testid="stSidebar"] { background-color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- DIRECTORIES ---
BASE_DIR = Path(__file__).parent
MUSIC_DIR = BASE_DIR / "downloads"
MUSIC_DIR.mkdir(exist_ok=True)

# --- SIDEBAR (Matches PC Sidebar Layout) ---
with st.sidebar:
    st.markdown('<div class="slopify-logo">Slopify</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Spotify but sloppy</div>', unsafe_allow_html=True)
    
    # GIF LOGIC (Matches self.change_gif from PC)
    gif_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith('.gif')]
    if gif_files:
        if 'current_gif' not in st.session_state:
            st.session_state.current_gif = random.choice(gif_files)
        
        # Display the current GIF (like the AnimatedGIFLabel)
        st.image(str(BASE_DIR / st.session_state.current_gif), use_container_width=True)
        
        if st.button("🎲 CHANGE VIBE", use_container_width=True):
            st.session_state.current_gif = random.choice(gif_files)
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📥 Downloader")
    query = st.text_input("Song Name or Link", placeholder="Paste here...", key="url_input")
    
    # FETCH LOGIC (Matches download_logic from PC)
    if st.button("FETCH SONG", use_container_width=True):
        if query:
            with st.status("Decoding & Downloading...", expanded=True) as status:
                try:
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': str(MUSIC_DIR / '%(title)s.%(ext)s'),
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                        'quiet': True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Using ytsearch1 to match PC's behavior
                        ydl.download([f"ytsearch1:{query}"])
                    status.update(label="Success!", state="complete")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Status: Failed - {e}")

# --- MAIN VIEW (Matches PC Layout) ---
st.title("🎵 Your Library")

# Refresh list of songs (Matches self.refresh_list)
songs = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3', '.m4a', '.wav', '.opus', '.webm'))]

if not songs:
    st.info("Your library is empty. Use the sidebar to fetch some slop!")
else:
    # Song Selection (Simulates the Listbox double-click)
    selected_song = st.selectbox("Select Track", songs, label_visibility="collapsed")
    
    st.markdown(f"**Now Playing:** `{selected_song}`")
    
    # Audio Player (Mobile Native controls for Play/Pause/Seek)
    audio_path = MUSIC_DIR / selected_song
    try:
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
    except Exception as e:
        st.error(f"Could not play file: {e}")

    # Playlist Display (Visual list of what's in the downloads folder)
    st.markdown("---")
    st.markdown("### 📋 Playlist")
    for s in songs:
        # Highlight the currently selected song
        if s == selected_song:
            st.success(f"▶️ {s}")
        else:
            st.text(f"🔘 {s}")

# --- AUTO-REFRESH (Optional) ---
# Small delay to keep UI snappy
time.sleep(0.1)
