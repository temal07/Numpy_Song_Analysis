import streamlit as st
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from spotipy.exceptions import SpotifyException
import os

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-library-read user-library-modify user-read-currently-playing"
)

sp = spotipy.Spotify(auth_manager=sp_oauth)

st.title("Spotify Track Info & Liked Songs Checker")

# ------------- Current Song Info -------------
if st.button("Show Current Playing Song"):
    current_song = sp.current_user_playing_track()
    if current_song is None or current_song['item'] is None:
        st.warning("No Song is currently playing. Try turning on a song!")
    else:
        item = current_song['item']
        name = item['name']
        artist = ", ".join([artist['name'] for artist in item['artists']])
        album_name = item['album']['name']
        album_cover_image = item['album']['images'][0]['url']
        song_url = item['external_urls']['spotify']
        popularity = item.get('popularity', 'N/A')  # sometimes may not be present

        st.subheader("Current Song Information")
        st.write(f"**Name:** {name}")
        st.write(f"**Artist(s):** {artist}")
        st.write(f"**Album:** {album_name}")
        st.image(album_cover_image, width=200)
        st.write(f"**Popularity:** {popularity}/100")
        st.markdown(f"[Open in Spotify]({song_url})")

st.markdown("---")

# ------------- Get Music Data from URL -------------
input_song_url = st.text_input("Enter song URL to get info:")

if input_song_url:
    try:
        song_id = input_song_url.split("/track/")[1].split("?")[0]
        song_data = sp.track(song_id)
    except (SpotifyException, IndexError):
        st.error("Invalid Song URL. Please try again.")
    else:
        song_name = song_data['name']
        artist_names = [artist['name'] for artist in song_data['artists']]
        album_cover_url = song_data['album']['images'][0]['url']
        song_popularity = song_data['popularity']
        in_favourites = sp.current_user_saved_tracks_contains([song_id])[0]

        st.subheader("Song Information")
        st.write(f"**Song Name:** {song_name}")
        st.write(f"**Artist(s):** {', '.join(artist_names)}")
        st.image(album_cover_url, width=200)
        st.write(f"**Song Popularity:** {song_popularity}")
        st.write(f"**In 'Liked Songs':** {'Yes' if in_favourites else 'No'}")

st.markdown("---")

# ------------- Check/Add Song to Liked Songs -------------
track_url_input = st.text_input("Enter Song URL to check if in Liked Songs:")

if track_url_input:
    try:
        # Extract track ID from URL
        track_id = track_url_input.split("/track/")[1].split("?")[0]
        
        # Validate the track exists
        sp.track(track_id)
        
        # Check if track is in liked songs
        in_liked = sp.current_user_saved_tracks_contains([track_id])[0]
    except (SpotifyException, IndexError):
        st.error("Invalid Track URL. Please try again.")
    else:
        if in_liked:
            st.info("This track is already in your Liked Songs.")
        else:
            if st.button("Add to Liked Songs"):
                sp.current_user_saved_tracks_add([track_id])
                st.success("Track added to your Liked Songs!")
