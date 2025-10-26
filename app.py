import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask, session, request, redirect, render_template, jsonify, url_for
from dotenv import load_dotenv
from functools import wraps
from flask import make_response
import spotipy
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build


# Load environment variables
load_dotenv()
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

# --- Helper Functions (Scraping) ---
def scrape_thaiticketmajor(search_query=""):
    """ A reusable scraping function. """
    base_url = "https://www.thaiticketmajor.com/concert/"
    search_url = f"{base_url}?keyword={search_query}" if search_query else base_url
    
    found_concerts = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        events = soup.find_all('div', class_='event-card-box') # Use event-card-box as per scraper.py
        
        for i, event in enumerate(events):
            name_tag = event.find('h3', class_='event-card-title')
            venue_tag = event.find('p', class_='event-card-venue')
            url_tag = event.find('a', href=True)
            
            if name_tag and url_tag:
                event_url = url_tag['href']
                if not event_url.startswith('http'):
                    event_url = "https://www.thaiticketmajor.com" + event_url

                found_concerts.append({
                    "id": f"concert-{i}-{name_tag.text.strip()}",
                    "artist": name_tag.text.strip().split(' ')[0].upper(),
                    "name": name_tag.text.strip(),
                    "venue": venue_tag.text.strip() if venue_tag else "N/A",
                    "date": datetime.datetime.now().isoformat(), # Placeholder
                    "url": event_url
                })
        return found_concerts
    except Exception as e:
        print(f"SCRAPING FAILED for query '{search_query}': {e}")
        return []

# --- Google & Spotify Setup ---
def create_spotify_oauth():
    return spotipy.SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID", "").strip(),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET", "").strip(),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "").strip(),
        scope="user-top-read",
        show_dialog=True,
        cache_path=None
    )

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

# --- Main & Auth Routes ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/login')
def login():
    # Clear existing Spotify token info to force a fresh login
    if "spotify_token_info" in session:
        session.pop("spotify_token_info", None)
    return redirect(create_spotify_oauth().get_authorize_url())

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/callback')
def callback():
    if 'error' in request.args:
        # User cancelled or an error occurred during authorization
        if "spotify_token_info" in session:
            session.pop("spotify_token_info", None)
        # Redirect to homepage
        return redirect('/')

    # Proceed with normal token exchange if no error
    # [ไฟล์ app.py บรรทัด 118] <-- นี่คือจุดแก้ไขที่ 1
    session["spotify_token_info"] = create_spotify_oauth().get_access_token(request.args.get('code'), as_dict=True, check_cache=False)
    session.permanent = True
    return redirect('/')

@app.route('/google-login')
def google_login():
    print(f"DEBUG: Generated Redirect URI for Google: {url_for('google_callback', _external=True)}")
    authorization_url, state = create_google_flow().authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/google-callback')
def google_callback():
    flow = create_google_flow()
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['google_credentials'] = { 'token': creds.token, 'refresh_token': creds.refresh_token, 'token_uri': creds.token_uri, 'client_id': creds.client_id, 'client_secret': creds.client_secret, 'scopes': creds.scopes }
    return redirect('/')



# --- API Endpoints ---
@app.route('/api/auth-status')
@nocache
def auth_status(): return jsonify({ 'spotify_logged_in': 'spotify_token_info' in session, 'google_logged_in': 'google_credentials' in session })

@app.route('/api/concerts')
def get_concerts():
    concerts = scrape_thaiticketmajor()
    if not concerts:
        print("Scraping failed. Falling back to local concerts.json")
        try:
            with open('concerts.json', 'r', encoding='utf-8') as f:
                concerts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            concerts = []
    return jsonify(concerts)

@app.route('/api/spotify/top-artists')
@nocache
def get_top_artists():
    token_info = session.get("spotify_token_info")
    if not token_info: return jsonify({"error": "Not logged in"}), 401
    
    sp_oauth = create_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        # <-- นี่คือจุดแก้ไขที่ 2
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'], check_cache=False)
        session["spotify_token_info"] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_top_artists(limit=5, time_range='short_term')
    artists = [{'name': item['name'], 'image_url': item['images'][0]['url'] if item['images'] else '', 'spotify_url': item['external_urls']['spotify']} for item in results['items']]
    return jsonify(artists)

@app.route('/api/add-to-calendar', methods=['POST'])
def add_to_calendar():
    if 'google_credentials' not in session: return jsonify({'error': 'User not authenticated with Google'}), 401
    credentials = google.oauth2.credentials.Credentials(**session['google_credentials'])
    try:
        service = build('calendar', 'v3', credentials=credentials)
        concert = request.json
        date_str = concert.get('date')
        event_time = None
        description = f"Link: {concert.get('url')}"

        # Try to parse ISO format
        try:
            event_time = datetime.datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            # If parsing fails, default to today at noon and add a note.
            event_time = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
            description += f"\n\nหมายเหตุ: ไม่สามารถประมวลผลวันที่ '{date_str}' ได้ กรุณาตรวจสอบและแก้ไขวันที่ในปฏิทินของคุณ"

        event = { 'summary': concert.get('name'), 'location': concert.get('venue'), 'description': description, 'start': {'dateTime': event_time.isoformat(), 'timeZone': 'Asia/Bangkok'}, 'end': {'dateTime': (event_time + datetime.timedelta(hours=2)).isoformat(), 'timeZone': 'Asia/BangKOK'}}
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return jsonify({'status': 'success', 'event_link': created_event.get('htmlLink')})
    except Exception as e:
        if 'invalid_grant' in str(e).lower():
            session.pop('google_credentials', None)
            return jsonify({'error': 'Google authentication failed or was revoked. Please log in again.'}), 401
        return jsonify({'error': f'Failed to create calendar event: {e}'}), 500



@app.route('/api/artist-concerts')
def get_artist_concerts():
    artist_name = request.args.get('artist', '')
    if not artist_name: return jsonify({"error": "Artist name is required."}), 400
    
    concerts = scrape_thaiticketmajor(search_query=artist_name)
    if not concerts:
        print(f"Live search for '{artist_name}' failed. Falling back to local concerts.json")
        try:
            with open('concerts.json', 'r', encoding='utf-8') as f:
                all_concerts = json.load(f)
                concerts = [c for c in all_concerts if artist_name.lower() in c['name'].lower()]
        except (FileNotFoundError, json.JSONDecodeError):
            concerts = []

    return jsonify(concerts)

if __name__ == '__main__':
    app.run(debug=True)