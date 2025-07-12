import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyPKCE
from spotipy.exceptions import SpotifyException

# ------------- PKCE AUTH SETUP -------------

CLIENT_ID = st.secrets["CLIENT_ID"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]
"""
sp_oauth = SpotifyPKCE(
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    scope="user-library-read user-library-modify user-read-currently-playing"
)

"""

if "sp_oauth" not in st.session_state:
    st.session_state.sp_oauth = SpotifyPKCE(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope="user-library-read user-library-modify user-read-currently-playing"
    )

sp_oauth = st.session_state.sp_oauth

# Handle callback after redirect
query_params = st.experimental_get_query_params()

if "code" in query_params:
    code = query_params["code"][0]
    try:
        token_info = sp_oauth.get_access_token(code)
        access_token = token_info["access_token"]
        sp = spotipy.Spotify(auth=access_token)
    except Exception as e:
        st.error(f"Auth Error: {e}")
        st.stop()
else:
    auth_url = sp_oauth.get_authorize_url()
    st.write("## 🎵 Authorize this app to access your Spotify account")
    st.markdown(f"[Click here to authorize 🎶]({auth_url})")
    st.stop()
# ------------- APP UI + FUNCTIONALITY -------------

st.title("🎶 Spotify Track Info & Liked Songs Manager")

# -- Show current playing song --
if st.button("Show Current Playing Song"):
    current_song = sp.current_user_playing_track()
    if current_song is None or current_song['item'] is None:
        st.warning("No song is currently playing.")
    else:
        item = current_song['item']
        name = item['name']
        artist = ", ".join([artist['name'] for artist in item['artists']])
        album_name = item['album']['name']
        album_cover_image = item['album']['images'][0]['url']
        song_url = item['external_urls']['spotify']
        popularity = item.get('popularity', 'N/A')

        st.subheader("Now Playing 🎧")
        st.write(f"**Name:** {name}")
        st.write(f"**Artist(s):** {artist}")
        st.write(f"**Album:** {album_name}")
        st.image(album_cover_image, width=200)
        st.write(f"**Popularity:** {popularity}/100")
        st.markdown(f"[Open in Spotify]({song_url})")

st.markdown("---")

# -- Get Song Info from URL --
song_url_input = st.text_input("🔍 Enter Spotify Track URL to get info:")

if song_url_input:
    try:
        song_id = song_url_input.split("/track/")[1].split("?")[0]
        song_data = sp.track(song_id)
    except (SpotifyException, IndexError):
        st.error("Invalid Spotify track URL.")
    else:
        song_name = song_data['name']
        artist_names = [artist['name'] for artist in song_data['artists']]
        album_cover_url = song_data['album']['images'][0]['url']
        song_popularity = song_data['popularity']
        in_favourites = sp.current_user_saved_tracks_contains([song_id])[0]

        st.subheader("Song Information 🎶")
        st.write(f"**Name:** {song_name}")
        st.write(f"**Artist(s):** {', '.join(artist_names)}")
        st.image(album_cover_url, width=200)
        st.write(f"**Popularity:** {song_popularity}/100")
        st.write(f"**In 'Liked Songs':** {'✅ Yes' if in_favourites else '❌ No'}")

st.markdown("---")

# -- Check & Add Song to Liked Songs --
track_url_input = st.text_input("❤️ Enter Spotify Track URL to check/add to Liked Songs:")

if track_url_input:
    try:
        track_id = track_url_input.split("/track/")[1].split("?")[0]
        sp.track(track_id)  # Validate track exists
        in_liked = sp.current_user_saved_tracks_contains([track_id])[0]
    except (SpotifyException, IndexError):
        st.error("Invalid Spotify track URL.")
    else:
        if in_liked:
            st.info("✅ This track is already in your Liked Songs.")
        else:
            if st.button("Add to Liked Songs ❤️"):
                sp.current_user_saved_tracks_add([track_id])
                st.success("🎉 Track added to your Liked Songs!")

