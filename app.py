import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask, session, request, redirect, render_template, jsonify, url_for
from dotenv import load_dotenv
import spotipy


# Load environment variables
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_very_strong_secret_key_123")

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
        client_id=os.getenv("SPOTIPY_CLIENT_ID"), client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"), scope="user-top-read"
    )

# --- Main & Auth Routes ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/login')
def login(): return redirect(create_spotify_oauth().get_authorize_url())

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

@app.route('/callback')
def callback(): 
    session["spotify_token_info"] = create_spotify_oauth().get_access_token(request.args.get('code'))
    return redirect('/')



# --- API Endpoints ---
@app.route('/api/auth-status')
def auth_status(): return jsonify({ 'spotify_logged_in': 'spotify_token_info' in session })

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
def get_top_artists():
    token_info = session.get("spotify_token_info")
    if not token_info: return jsonify({"error": "Not logged in"}), 401
    
    sp_oauth = create_spotify_oauth()
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session["spotify_token_info"] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.current_user_top_artists(limit=5, time_range='short_term')
    artists = [{'name': item['name'], 'image_url': item['images'][0]['url'] if item['images'] else '', 'spotify_url': item['external_urls']['spotify']} for item in results['items']]
    return jsonify(artists)



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

