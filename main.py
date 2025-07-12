import streamlit as st
import requests
import base64
import hashlib
import os
import urllib

# Load secrets
CLIENT_ID = st.secrets["CLIENT_ID"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]
SCOPE = "user-library-read user-library-modify user-read-currently-playing"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Generate code verifier/challenge
def generate_code_verifier():
    return base64.urlsafe_b64encode(os.urandom(64)).decode('utf-8').rstrip('=')

def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

# First run: setup PKCE
if "access_token" not in st.session_state:
    if "code_verifier" not in st.session_state:
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier)
        st.session_state.code_verifier = verifier

        # Build auth URL
        params = {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPE,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
        auth_url = AUTH_URL + "?" + urllib.parse.urlencode(params)
        st.write("## 🎵 Authorize this app to access your Spotify account")
        st.markdown(f"[Click here to authorize 🎶]({auth_url})")
        st.stop()

    # Check for redirect code
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"][0]
        verifier = st.session_state.code_verifier

        # Exchange code for access token
        data = {
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier,
        }
        response = requests.post(TOKEN_URL, data=data)
        if response.status_code == 200:
            token_info = response.json()
            st.session_state.access_token = token_info["access_token"]
            st.experimental_set_query_params()  # Clean the URL
            st.experimental_rerun()
        else:
            st.error(f"Token exchange failed: {response.json()}")
            st.stop()
    else:
        st.stop()

# At this point, authenticated
access_token = st.session_state.access_token
headers = {"Authorization": f"Bearer {access_token}"}

st.title("🎶 Spotify Track Info & Liked Songs Manager")

# Show current playing song
if st.button("Show Current Playing Song"):
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code != 200 or r.json() is None:
        st.warning("No song is currently playing.")
    else:
        data = r.json()
        item = data["item"]
        st.subheader("Now Playing 🎧")
        st.write(f"**Name:** {item['name']}")
        st.write(f"**Artist(s):** {', '.join([artist['name'] for artist in item['artists']])}")
        st.write(f"**Album:** {item['album']['name']}")
        st.image(item['album']['images'][0]['url'], width=200)
        st.write(f"**Popularity:** {item.get('popularity', 'N/A')}/100")
        st.markdown(f"[Open in Spotify]({item['external_urls']['spotify']})")

st.markdown("---")

# Get track info by URL
track_url = st.text_input("🔍 Enter Spotify Track URL to get info:")
if track_url:
    try:
        track_id = track_url.split("/track/")[1].split("?")[0]
        r = requests.get(f"https://api.spotify.com/v1/tracks/{track_id}", headers=headers)
        if r.status_code != 200:
            st.error("Track not found or invalid URL.")
        else:
            data = r.json()
            st.subheader("Track Information 🎶")
            st.write(f"**Name:** {data['name']}")
            st.write(f"**Artist(s):** {', '.join([artist['name'] for artist in data['artists']])}")
            st.image(data['album']['images'][0]['url'], width=200)
            st.write(f"**Popularity:** {data['popularity']}/100")

            # Check if liked
            contains_r = requests.get(
                f"https://api.spotify.com/v1/me/tracks/contains?ids={track_id}",
                headers=headers
            )
            liked = contains_r.json()[0]
            st.write(f"**In Liked Songs:** {'✅ Yes' if liked else '❌ No'}")

            # Add to liked songs
            if not liked:
                if st.button("❤️ Add to Liked Songs"):
                    add_r = requests.put(
                        f"https://api.spotify.com/v1/me/tracks?ids={track_id}",
                        headers=headers
                    )
                    if add_r.status_code == 200:
                        st.success("Added to Liked Songs!")
    except Exception as e:
        st.error(f"Invalid Spotify track URL: {e}")
