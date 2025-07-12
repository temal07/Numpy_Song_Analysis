import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyPKCE
from spotipy.exceptions import SpotifyException

# ------------- Spotify PKCE AUTH SETUP -------------
CLIENT_ID = st.secrets["CLIENT_ID"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]
SCOPE = "user-library-read user-library-modify user-read-currently-playing"

# Initialize session state variables
if "sp_oauth" not in st.session_state:
    st.session_state.sp_oauth = SpotifyPKCE(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
    )
if "access_token" not in st.session_state:
    st.session_state.access_token = None

sp_oauth = st.session_state.sp_oauth

# Check if redirected back with ?code=xxx
query_params = st.query_params
if "code" in query_params:
    code = query_params["code"][0]
    try:
        token_info = sp_oauth.get_access_token(code)
        st.session_state.access_token = token_info["access_token"]
        st.experimental_set_query_params()  # clears URL query params
        st.experimental_rerun()  # rerun to refresh with token
    except Exception as e:
        st.error(f"Auth Error: {e}")
        st.stop()

# If not logged in yet — show auth link
if not st.session_state.access_token:
    auth_url = sp_oauth.get_authorize_url()
    st.title("🎵 Spotify Song Checker")
    st.markdown(f"[Click here to authorize 🎶]({auth_url})")
    st.stop()

# ------------- APP FUNCTIONALITY -------------
sp = spotipy.Spotify(auth=st.session_state.access_token)

st.title("🎶 Spotify Track Info & Liked Songs Manager")

# -- Show current playing song --
if st.button("Show Current Playing Song"):
    current_song = sp.current_user_playing_track()
    if current_song is None or current_song['item'] is None:
        st.warning("No song is currently playing.")
    else:
        item = current_song['item']
        st.subheader("Now Playing 🎧")
        st.write(f"**Name:** {item['name']}")
        st.write(f"**Artist(s):** {', '.join([a['name'] for a in item['artists']])}")
        st.write(f"**Album:** {item['album']['name']}")
        st.image(item['album']['images'][0]['url'], width=200)
        st.markdown(f"[Open in Spotify]({item['external_urls']['spotify']})")

st.markdown("---")

# -- Get Song Info from URL --
song_url_input = st.text_input("🔍 Enter Spotify Track URL to get info:")

if song_url_input:
    try:
        song_id = song_url_input.split("/track/")[1].split("?")[0]
        song_data = sp.track(song_id)
        st.subheader("Track Info 🎶")
        st.write(f"**Name:** {song_data['name']}")
        st.write(f"**Artist(s):** {', '.join([a['name'] for a in song_data['artists']])}")
        st.image(song_data['album']['images'][0]['url'], width=200)
    except (SpotifyException, IndexError):
        st.error("Invalid Spotify track URL.")

st.markdown("---")

# -- Check/Add Song to Liked Songs --
track_url_input = st.text_input("❤️ Enter Spotify Track URL to check/add to Liked Songs:")

if track_url_input:
    try:
        track_id = track_url_input.split("/track/")[1].split("?")[0]
        sp.track(track_id)  # Validate track exists
        in_liked = sp.current_user_saved_tracks_contains([track_id])[0]
        if in_liked:
            st.info("✅ This track is already in your Liked Songs.")
        else:
            if st.button("Add to Liked Songs ❤️"):
                sp.current_user_saved_tracks_add([track_id])
                st.success("🎉 Track added to your Liked Songs!")
    except (SpotifyException, IndexError):
        st.error("Invalid Spotify track URL.")
