import os
import json
import datetime
import time
import re
from functools import wraps
from uuid import uuid4
import requests
from bs4 import BeautifulSoup
from flask import Flask, session, request, redirect, render_template, jsonify, url_for, make_response
from dotenv import load_dotenv
import spotipy
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
LOAD_DOTENV_RESULT = load_dotenv()
print(f"load_dotenv result: {LOAD_DOTENV_RESULT}")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_very_strong_secret_key_123")
app.permanent_session_lifetime = datetime.timedelta(days=31)

def nocache(view):
    @wraps(view)
    def no_cache_impl(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return no_cache_impl

# ✅ ThaiTicketMajor Scraper
def scrape_thaiticketmajor(search_query=""):
    base_url = "https://www.thaiticketmajor.com/concert/"
    search_url = f"{base_url}?keyword={search_query}" if search_query else base_url
    found_concerts = []

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        events = soup.select('div.event-item')

        for i, event in enumerate(events):
            name_tag = event.find('a', class_='title')
            name = name_tag.text.strip() if name_tag else "N/A"

            url_tag = event.find('a', class_='box-img')
            event_url = url_tag['href'] if url_tag and 'href' in url_tag.attrs else ""
            if not event_url.startswith('http'):
                event_url = "https://www.thaiticketmajor.com" + event_url

            img_tag = event.find('img', class_='lazy')
            image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
            if not image_url.startswith('http'):
                image_url = "https://www.thaiticketmajor.com" + image_url

            booking_tag = event.find('a', class_='btn-buynow')
            booking_url = ""
            if booking_tag:
                onclick_attr = booking_tag.get('onclick')
                if onclick_attr:
                    match = re.search(r"'(https://booking\.thaiticketmajor\.com/booking/3m/zones\.php\?query=\d+)'", onclick_attr)
                    if match:
                        booking_url = match.group(1)
                if not booking_url:
                    href_attr = booking_tag.get('href')
                    if href_attr and href_attr != "javascript:void(0);":
                        booking_url = "https://www.thaiticketmajor.com" + href_attr if not href_attr.startswith('http') else href_attr

            venue_tag = event.find('a', class_='venue') or event.find('span', class_='venue')
            venue = venue_tag.find('span').text.strip() if venue_tag and venue_tag.find('span') else "N/A"

            found_concerts.append({
                "id": f"concert-{i}-{name}",
                "artist": name.split(' ')[0].upper(),
                "name": name,
                "venue": venue,
                "date": datetime.datetime.now().isoformat(), 
                "url": event_url,
                "image_url": image_url,
                "booking_url": booking_url if booking_url else event_url
            })

        return found_concerts

    except requests.exceptions.RequestException as e:
        print(f"SCRAPING FAILED for query '{search_query}': {e}")
        return []

### ✅ Spotify OAuth Session
def create_spotify_oauth():
    user_cache = f".cache-{session.get('session_id', 'anon')}"
    return spotipy.SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID", "").strip(),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET", "").strip(),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "").strip(),
        scope="user-top-read",
        show_dialog=True,
        cache_path=user_cache
    )

### ✅ Google OAuth
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
def create_google_flow():
    return google_auth_oauthlib.flow.Flow.from_client_config(
        {"web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }},
        scopes=SCOPES,
        redirect_uri=url_for('google_callback', _external=True)
    )

### ✅ Home
@app.route('/')
def home():
    if "session_id" not in session:
        session["session_id"] = str(uuid4())

    if not os.path.exists('favorite_artists.json'):
        with open('favorite_artists.json', 'w', encoding='utf-8') as f:
            json.dump([], f)

    with open('favorite_artists.json', 'r', encoding='utf-8') as f:
        favorite_artists = json.load(f)

    return render_template('index.html', favorite_artists=favorite_artists)

### ✅ Login Spotify
@app.route('/login')
def login():
    session.pop("spotify_token_info", None)
    return redirect(create_spotify_oauth().get_authorize_url())

### ✅ Logout
@app.route('/logout')
def logout():
    try:
        cache_file = f".cache-{session.get('session_id')}"
        if cache_file and os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"🧹 Removed user cache: {cache_file}")
    except: pass

    session.clear()
    return redirect('/')

### ✅ Spotify Callback
@app.route('/callback')
def callback():
    if 'error' in request.args:
        session.pop("spotify_token_info", None)
        return redirect('/')

    code = request.args.get('code')
    sp_oauth = create_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)

    session["spotify_token_info"] = token_info
    session.permanent = True

    print("✅ Spotify Login Successful")
    return redirect('/')

### ✅ Get Top Artists
@app.route('/api/spotify/top-artists')
@nocache
def get_top_artists():
    token_info = session.get("spotify_token_info")
    if not token_info:
        return jsonify({"error": "Not logged in"}), 401

    sp_oauth = create_spotify_oauth()

    if sp_oauth.is_token_expired(token_info):
        refreshed = sp_oauth.refresh_access_token(token_info["refresh_token"])
        token_info.update(refreshed)
        session["spotify_token_info"] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_top_artists(limit=5)

    artists = [{
        "name": item["name"],
        "image_url": item["images"][0]["url"] if item["images"] else "",
        "spotify_url": item["external_urls"]["spotify"]
    } for item in results["items"]]

    return jsonify(artists)

### ✅ Artist Bookmarks
@app.route('/add_artist', methods=['POST'])
def add_artist():
    artist_name = request.form.get('artist_name')
    if not artist_name: return redirect('/')

    if not os.path.exists('favorite_artists.json'):
        with open('favorite_artists.json', 'w', encoding='utf-8') as f:
            json.dump([], f)

    with open('favorite_artists.json', 'r+', encoding='utf-8') as f:
        favorite_artists = json.load(f)
        if not any(a['name'] == artist_name for a in favorite_artists):
            favorite_artists.append({'name': artist_name})
            f.seek(0)
            json.dump(favorite_artists, f, ensure_ascii=False, indent=4)

    return redirect('/')

@app.route('/api/artist/delete', methods=['POST'])
def delete_artist():
    name = request.json.get('name')
    if not name:
        return jsonify({'error': 'Artist name required'}), 400

    if not os.path.exists('favorite_artists.json'):
        return jsonify({'error': 'file missing'}), 404

    with open('favorite_artists.json', 'r+', encoding='utf-8') as f:
        artist_list = json.load(f)
        new_list = [a for a in artist_list if a['name'] != name]

        f.seek(0)
        f.truncate()
        json.dump(new_list, f, ensure_ascii=False, indent=4)

    return jsonify({'status': 'success'})

### ✅ Concert API
@app.route('/api/concerts')
def get_concerts():
    concerts = scrape_thaiticketmajor()
    if not concerts:
        try:
            with open('concerts.json', 'r', encoding='utf-8') as f:
                concerts = json.load(f)
        except:
            concerts = []

    return jsonify(concerts)

### ✅ Google Add Calendar
@app.route('/api/add-to-calendar', methods=['POST'])
def add_to_calendar():
    if 'google_credentials' not in session:
        return jsonify({'error': 'Login Google first'}), 401
    
    credentials = google.oauth2.credentials.Credentials(**session['google_credentials'])
    service = build('calendar', 'v3', credentials=credentials)

    data = request.json
    date_str = data.get('date')

    try:
        event_time = datetime.datetime.fromisoformat(date_str)
    except:
        event_time = datetime.datetime.now().replace(hour=12)

    event = {
        'summary': data.get('name'),
        'location': data.get('venue'),
        'start': {'dateTime': event_time.isoformat(), 'timeZone': 'Asia/Bangkok'},
        'end': {'dateTime': (event_time + datetime.timedelta(hours=2)).isoformat(), 'timeZone': 'Asia/Bangkok'}
    }

    created = service.events().insert(calendarId='primary', body=event).execute()
    return jsonify({'status': 'success', 'event_link': created.get('htmlLink')})

### ✅ Search Artist Concerts
@app.route('/api/artist-concerts')
def get_artist_concerts():
    artist = request.args.get('artist', '')
    if not artist:
        return jsonify({"error": "Artist name required"}), 400

    concerts = scrape_thaiticketmajor(search_query=artist)

    filtered = [c for c in concerts if artist.lower() in c['name'].lower()]

    if not filtered:
        try:
            with open('concerts.json', 'r', encoding='utf-8') as f:
                all_concerts = json.load(f)
                filtered = [c for c in all_concerts if artist.lower() in c['name'].lower()]
        except:
            filtered = []

    return jsonify(filtered)

if __name__ == '__main__':
    app.run(debug=True)
