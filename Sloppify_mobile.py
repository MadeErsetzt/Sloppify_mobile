import streamlit as st
import os
import random
import yt_dlp
from pathlib import Path
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Slopify Mobile", layout="wide", initial_sidebar_state="expanded")

# --- STEP 1: MATCHING THE DESKTOP VIBE (CSS) ---
st.markdown("""
    <style>
    /* Pulsing Red Logo - Matching PC Version */
    @keyframes pulse {
        0% { color: #550000; }
        50% { color: #ff0000; }
        100% { color: #550000; }
    }
    .slopify-logo {
        font-family: 'UnifrakturCook', 'serif';
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
    /* Dark Theme Fixes */
    .stApp { background-color: #121212; }
    [data-testid="stSidebar"] { background-color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- DIRECTORIES ---
BASE_DIR = Path(__file__).parent
MUSIC_DIR = BASE_DIR / "downloads"
MUSIC_DIR.mkdir(exist_ok=True)

# --- SIDEBAR (Matches PC Sidebar) ---
with st.sidebar:
    st.markdown('<div class="slopify-logo">Slopify</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Premium Sloppy Player</div>', unsafe_allow_html=True)
    
    # GIF LOGIC (Interactive like PC)
    gif_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith('.gif')]
    if gif_files:
        if 'current_gif' not in st.session_state:
            st.session_state.current_gif = random.choice(gif_files)
        
        st.image(str(BASE_DIR / st.session_state.current_gif), use_container_width=True)
        
        if st.button("🎲 CHANGE VIBE", use_container_width=True):
            st.session_state.current_gif = random.choice(gif_files)
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📥 Downloader")
    query = st.text_input("Song Name or Link", placeholder="Paste here...", key="url_input")
    
    if st.button("FETCH SONG", use_container_width=True):
        if query:
            with st.status("Downloading...", expanded=True) as status:
                try:
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': str(MUSIC_DIR / '%(title)s.%(ext)s'),
                        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
                        'quiet': True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([f"ytsearch1:{query}"])
                    status.update(label="Success!", state="complete")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- MAIN VIEW (Matches PC Layout) ---
st.title("🎵 Your Library")

songs = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(('.mp3', '.m4a', '.wav'))]

if not songs:
    st.info("Your library is empty. Use the sidebar to fetch some slop!")
else:
    # Song Selection (Matches Listbox)
    selected_song = st.selectbox("Select Track", songs, label_visibility="collapsed")
    
    st.markdown(f"**Now Playing:** `{selected_song}`")
    
    # Audio Player (Mobile Native)
    audio_path = MUSIC_DIR / selected_song
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3")

    # Playlist Display
    st.markdown("---")
    st.markdown("### 📋 Playlist")
    for s in songs:
        icon = "▶️" if s == selected_song else "🔘"
        st.text(f"{icon} {s}")
