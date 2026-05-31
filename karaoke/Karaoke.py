import re
import json
import streamlit as st
import syncedlyrics
from googleapiclient.discovery import build
import io
import os
from dotenv import load_dotenv

load_dotenv()


YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def _buscar_video_api(query):
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(q=query, part='snippet', maxResults=1, type='video')
        response = request.execute()
        if response['items']:
            return response['items'][0]['id']['videoId']
        return None
    except:
        return None


def render_karaoke(cancion, artista):
    if cancion and artista:
        with st.spinner("📡 Sincronizando escenario..."):
            video_id = _buscar_video_api(f"{cancion} {artista} karaoke instrumental")
            lrc_data = syncedlyrics.search(f"{cancion} {artista}", providers=['lrclib'])

            if video_id and lrc_data:
                lyrics_list = []
                for line in lrc_data.split('\n'):
                    match = re.search(r'\[(\d+):(\d+\.\d+)\](.*)', line)
                    if match:
                        time_sec = int(match.group(1)) * 60 + float(match.group(2))
                        text = match.group(3).strip()
                        if text:
                            lyrics_list.append({'time': time_sec, 'text': text})

                lyrics_json = json.dumps(lyrics_list)

                st.video(f"https://www.youtube.com/watch?v={video_id}")

                st.markdown(f"""
                    <div class="lyric-box">
                        <h1 id="lyric-text" style="color: white; font-size: 35px; min-height: 50px;">¡Dale al Play arriba!</h1>
                        <p id="lyric-next" style="color: #535353; font-size: 18px;"></p>
                    </div>

                    <script>
                        const syncLyrics = () => {{
                            const video = window.parent.document.querySelector('video');
                            const lyrics = {lyrics_json};
                            const display = window.parent.document.getElementById('lyric-text');
                            const nextDisplay = window.parent.document.getElementById('lyric-next');

                            if (video) {{
                                video.ontimeupdate = () => {{
                                    const currentTime = video.currentTime;
                                    let activeIdx = -1;
                                    for (let i = 0; i < lyrics.length; i++) {{
                                        if (currentTime >= lyrics[i].time) activeIdx = i;
                                        else break;
                                    }}
                                    if (activeIdx !== -1) {{
                                        display.innerText = lyrics[activeIdx].text;
                                        nextDisplay.innerText = lyrics[activeIdx+1] ? "Siguiente: " + lyrics[activeIdx+1].text : "";
                                    }}
                                }};
                            }}
                        }};
                        setTimeout(syncLyrics, 2000);
                    </script>
                """, unsafe_allow_html=True)
            else:
                st.error("No se pudo encontrar el video o la letra sincronizada.")
    else:
        st.warning("Introduce el nombre de la canción y el artista ⚠️")
