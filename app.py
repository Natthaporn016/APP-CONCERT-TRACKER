import os
import json
import datetime
import time
import re
from functools import wraps

import requests
from bs4 import BeautifulSoup
from flask import Flask, session, request, redirect, render_template, jsonify, url_for, make_response
from dotenv import load_dotenv
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
def home():
    if not os.path.exists('favorite_artists.json'):
        with open('favorite_artists.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open('favorite_artists.json', 'r', encoding='utf-8') as f:
        favorite_artists = json.load(f)
    return render_template('index.html', favorite_artists=favorite_artists)

@app.route('/logout')
def logout(): 
    session.clear()
    # Add a cache-busting parameter to the redirect
    return redirect(f'/?logout=true&_t={time.time()}')

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

@app.route('/api/auth-status')
@nocache
def auth_status():
    return jsonify({ 'google_logged_in': 'google_credentials' in session })





@app.route('/api/add-to-calendar', methods=['POST'])
def add_to_calendar():
    if 'google_credentials' not in session:
        return jsonify({'error': 'User not authenticated with Google'}), 401
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
    except HttpError as e:
        if e.resp.status == 401:
            session.pop('google_credentials', None)
            return jsonify({'error': 'Google authentication failed or was revoked. Please log in again.'}), 401
        return jsonify({'error': f'Failed to create calendar event: {e}'}), 500
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500



@app.route('/api/artist-concerts')



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

if __name__ == '__main__':
    app.run(debug=True)