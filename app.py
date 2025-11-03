import os
import json
import datetime
import time
<<<<<<< HEAD
import re
from functools import wraps

=======
>>>>>>> e407f12 (feat: update top artists API logs)
import requests
from bs4 import BeautifulSoup
from flask import Flask, session, request, redirect, render_template, jsonify, url_for, make_response
from dotenv import load_dotenv
<<<<<<< HEAD
=======
from functools import wraps
from uuid import uuid4
import spotipy
>>>>>>> e407f12 (feat: update top artists API logs)
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

### ✅ ThaiTicketMajor Scraper
def scrape_thaiticketmajor(search_query=""):
    base_url = "https://www.thaiticketmajor.com/concert/"
    search_url = f"{base_url}?keyword={search_query}" if search_query else base_url
    found_concerts = []

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
<<<<<<< HEAD
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
                        if not href_attr.startswith('http'):
                            booking_url = "https://www.thaiticketmajor.com" + href_attr
                        else:
                            booking_url = href_attr

            venue_tag = event.find('a', class_='venue') or event.find('span', class_='venue')
            venue = venue_tag.find('span').text.strip() if venue_tag and venue_tag.find('span') else "N/A"

            found_concerts.append({
                "id": f"concert-{i}-{name}",
                "artist": name.split(' ')[0].upper(),
                "name": name,
                "venue": venue,
                "date": datetime.datetime.now().isoformat(), # Placeholder
                "url": event_url,
                "image_url": image_url,
                "booking_url": booking_url if booking_url else event_url
            })
        return found_concerts
    except requests.exceptions.RequestException as e:
        print(f"SCRAPING FAILED for query '{search_query}': {e}")
        return []

def get_artist_image(artist_name):
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    print(f"Spotify Client ID: {client_id}") # Log Client ID

    if not client_id or not client_secret:
        print("Spotify API credentials not found in .env file.")
        return "https://via.placeholder.com/150"

    # Get access token
    auth_url = 'https://accounts.spotify.com/api/token'
    try:
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        }, timeout=10)
        auth_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        auth_response_data = auth_response.json()
        print(f"Spotify Auth Response: {auth_response_data}") # Log auth response
        access_token = auth_response_data.get('access_token')
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token from Spotify: {e}")
        return "https://via.placeholder.com/150"

    if not access_token:
        print("Failed to get access token from Spotify.")
        return "https://via.placeholder.com/150"

    # Search for artist
    search_url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': artist_name,
        'type': 'artist',
        'limit': 1
    }
    try:
        search_response = requests.get(search_url, headers=headers, params=params, timeout=10)
        search_response.raise_for_status()
        search_results = search_response.json()
        print(f"Spotify Search Results: {search_results}") # Log search results
    except requests.exceptions.RequestException as e:
        print(f"Error searching for artist on Spotify: {e}")
        return "https://via.placeholder.com/150"

    try:
        image_url = search_results['artists']['items'][0]['images'][0]['url']
        print(f"Found image URL on Spotify: {image_url}")
        return image_url
    except (KeyError, IndexError):
        print(f"Could not find artist image for {artist_name} on Spotify.")
        return "https://via.placeholder.com/150"

# --- Google Setup ---
=======
        events = soup.find_all('div', class_='event-card-box')

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
                    "date": datetime.datetime.now().isoformat(), 
                    "url": event_url
                })
        return found_concerts
    except Exception as e:
        print(f"SCRAPING FAILED: {e}")
        return []

### ✅ Spotify OAuth Manager (Session-based cache)
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
>>>>>>> e407f12 (feat: update top artists API logs)
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

### ✅ Home - Create session per user
@app.route('/')
def home():
<<<<<<< HEAD
    if not os.path.exists('favorite_artists.json'):
        with open('favorite_artists.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open('favorite_artists.json', 'r', encoding='utf-8') as f:
        favorite_artists = json.load(f)
    return render_template('index.html', favorite_artists=favorite_artists)
=======
    if "session_id" not in session:
        session["session_id"] = str(uuid4())
    return render_template('index.html')

### ✅ Spotify Login
@app.route('/login')
def login():
    session.pop("spotify_token_info", None)
    return redirect(create_spotify_oauth().get_authorize_url())
>>>>>>> e407f12 (feat: update top artists API logs)

### ✅ Logout + clear cache fully
@app.route('/logout')
<<<<<<< HEAD
def logout(): 
    session.clear()
    # Add a cache-busting parameter to the redirect
    return redirect(f'/?logout=true&_t={time.time()}')
=======
def logout():
    try:
        cache_file = f".cache-{session.get('session_id')}"
        if cache_file and os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"🧹 Removed user cache: {cache_file}")
    except:
        pass

    session.clear()
    return redirect('/')

### ✅ Spotify OAuth Callback
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

### ✅ API: Top Artists
@app.route('/api/spotify/top-artists')
@nocache
def get_top_artists():
    token_info = session.get("spotify_token_info")
    if not token_info:
        return jsonify({"error": "Not logged in"}), 401

    sp_oauth = create_spotify_oauth()

    if sp_oauth.is_token_expired(token_info):
        refreshed_token = sp_oauth.refresh_access_token(token_info["refresh_token"])
        token_info.update(refreshed_token)
        session["spotify_token_info"] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_top_artists(limit=5)

    artists = [{
        "name": item["name"],
        "image_url": item["images"][0]["url"] if item["images"] else "",
        "spotify_url": item["external_urls"]["spotify"]
    } for item in results["items"]]

    return jsonify(artists)
>>>>>>> e407f12 (feat: update top artists API logs)

### ✅ Google Auth Routes
@app.route('/google-login')
def google_login():
    authorization_url, state = create_google_flow().authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/google-callback')
def google_callback():
    flow = create_google_flow()
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['google_credentials'] = creds_to_dict(creds)
    return redirect('/')

def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes,
    }

<<<<<<< HEAD

@app.route('/add_artist', methods=['GET', 'POST'])
def add_artist():
    if request.method == 'POST':
        artist_name = request.form.get('artist_name')
        if artist_name:
            if not os.path.exists('favorite_artists.json'):
                with open('favorite_artists.json', 'w', encoding='utf-8') as f:
                    json.dump([], f)
            with open('favorite_artists.json', 'r+', encoding='utf-8') as f:
                favorite_artists = json.load(f)
                if not any(artist['name'] == artist_name for artist in favorite_artists):
                    print(f"Artist '{artist_name}' is new. Fetching image...")
                    image_url = get_artist_image(artist_name)
                    favorite_artists.append({'name': artist_name, 'image_url': image_url})
                    f.seek(0)
                    json.dump(favorite_artists, f, ensure_ascii=False, indent=4)
                else:
                    print(f"Artist '{artist_name}' already exists in favorites.")
        return redirect(url_for('home'))
    return render_template('add_artist.html')

@app.route('/api/artist/delete', methods=['POST'])
def delete_artist():
    artist_name = request.json.get('name')
    if not artist_name:
        return jsonify({'error': 'Artist name is required'}), 400

    if not os.path.exists('favorite_artists.json'):
        return jsonify({'error': 'Favorite artists file not found'}), 404

    with open('favorite_artists.json', 'r+', encoding='utf-8') as f:
        favorite_artists = json.load(f)
        original_count = len(favorite_artists)
        favorite_artists = [artist for artist in favorite_artists if artist['name'] != artist_name]
        
        if len(favorite_artists) < original_count:
            f.seek(0)
            f.truncate()
            json.dump(favorite_artists, f, ensure_ascii=False, indent=4)
            return jsonify({'status': 'success', 'message': f'Artist {artist_name} deleted'})
        else:
            return jsonify({'error': f'Artist {artist_name} not found'}), 404



# --- API Endpoints ---
@app.route('/api/concerts', endpoint='api_get_concerts')
=======
### ✅ Auth Check
@app.route('/api/auth-status')
@nocache
def auth_status():
    return jsonify({
        'spotify_logged_in': 'spotify_token_info' in session,
        'google_logged_in': 'google_credentials' in session
    })

### ✅ Concert Fetch
@app.route('/api/concerts')
>>>>>>> e407f12 (feat: update top artists API logs)
def get_concerts():
    concerts = scrape_thaiticketmajor()
    if not concerts:
        try:
            with open('concerts.json', 'r', encoding='utf-8') as f:
                concerts = json.load(f)
        except:
            concerts = []



    return jsonify(concerts)

<<<<<<< HEAD
@app.route('/api/auth-status')
@nocache
def auth_status():
    return jsonify({ 'google_logged_in': 'google_credentials' in session })





=======
### ✅ Calendar Add
>>>>>>> e407f12 (feat: update top artists API logs)
@app.route('/api/add-to-calendar', methods=['POST'])
def add_to_calendar():
    if 'google_credentials' not in session:
        return jsonify({'error': 'User not authenticated with Google'}), 401
<<<<<<< HEAD
=======
    
>>>>>>> e407f12 (feat: update top artists API logs)
    credentials = google.oauth2.credentials.Credentials(**session['google_credentials'])
    service = build('calendar', 'v3', credentials=credentials)

    concert = request.json
    date_str = concert.get('date')

    try:
<<<<<<< HEAD
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
    except HttpError as e:
        if e.resp.status == 401:
            session.pop('google_credentials', None)
            return jsonify({'error': 'Google authentication failed or was revoked. Please log in again.'}), 401
        return jsonify({'error': f'Failed to create calendar event: {e}'}), 500
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500
=======
        event_time = datetime.datetime.fromisoformat(date_str)
    except:
        event_time = datetime.datetime.now().replace(hour=12)
>>>>>>> e407f12 (feat: update top artists API logs)

    event = {
        'summary': concert.get('name'),
        'location': concert.get('venue'),
        'start': {'dateTime': event_time.isoformat(), 'timeZone': 'Asia/Bangkok'},
        'end': {'dateTime': (event_time + datetime.timedelta(hours=2)).isoformat(), 'timeZone': 'Asia/Bangkok'}
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return jsonify({'status': 'success', 'event_link': created_event.get('htmlLink')})

### ✅ Artist Concert Search
@app.route('/api/artist-concerts')
<<<<<<< HEAD



def get_artist_concerts():



    artist_name = request.args.get('artist', '')



    if not artist_name:



        return jsonify({"error": "Artist name is required."}), 400



    



    concerts = scrape_thaiticketmajor(search_query=artist_name)







    # Filter the concerts by artist name, because thaiticketmajor returns all concerts if the artist is not found.



    filtered_concerts = [c for c in concerts if artist_name.lower() in c['name'].lower()]







    if not filtered_concerts:



        print(f"Live search for '{artist_name}' failed or returned no results. Falling back to local concerts.json")



        try:



            with open('concerts.json', 'r', encoding='utf-8') as f:



                all_concerts = json.load(f)



                # Also filter the local file



                filtered_concerts = [c for c in all_concerts if artist_name.lower() in c['name'].lower()]



        except (FileNotFoundError, json.JSONDecodeError):



            filtered_concerts = []







    return jsonify(filtered_concerts)
=======
def get_artist_concerts():
    artist_name = request.args.get('artist', '')
    if not artist_name:
        return jsonify({"error": "Artist name required"}), 400

    concerts = scrape_thaiticketmajor(search_query=artist_name)
    return jsonify(concerts)
>>>>>>> e407f12 (feat: update top artists API logs)

if __name__ == '__main__':
    app.run(debug=True)
