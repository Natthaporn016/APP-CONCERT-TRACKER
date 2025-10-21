import requests
from bs4 import BeautifulSoup
import json
import sys
import datetime

# URL เป้าหมาย
BASE_URL = "https://www.thaiticketmajor.com/concert/"

def run_scraper(search_query=""):
    print(f"Starting scraper for query: '{search_query}'...")
    target_url = f"{BASE_URL}?keyword={search_query}" if search_query else BASE_URL
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Update selector for main event cards
        events = soup.select('div.event-container div.event-item')

        concert_data = []
        concert_id_counter = 1

        for i, event in enumerate(events):
            # Extract Name
            name_tag = event.find('a', class_='title')
            name = name_tag.text.strip() if name_tag else "N/A"

            # Extract URL
            url_tag = event.find('a', class_='box-img')
            event_url = url_tag['href'] if url_tag and 'href' in url_tag.attrs else ""
            if not event_url.startswith('http'):
                event_url = "https://www.thaiticketmajor.com" + event_url

            # Extract Image URL
            img_tag = event.find('img', class_='lazy')
            image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
            if not image_url.startswith('http'):
                image_url = "https://www.thaiticketmajor.com" + image_url

            # Extract Date
            date_span = event.find('span', class_='datetime')
            date = date_span.find('span').text.strip() if date_span and date_span.find('span') else "N/A"

            # Extract Venue
            venue_tag = event.find('a', class_='venue') or event.find('span', class_='venue')
            venue = venue_tag.find('span').text.strip() if venue_tag and venue_tag.find('span') else "N/A"

            # Extract Booking URL
            booking_tag = event.find('a', class_='btn-buynow')
            booking_url = booking_tag['href'] if booking_tag and 'href' in booking_tag.attrs else ""
            if not booking_url.startswith('http') and booking_url != "javascript:void(0);":
                booking_url = "https://www.thaiticketmajor.com" + booking_url
            elif booking_url == "javascript:void(0);": # Handle Sold Out/Coming Soon
                booking_url = ""


            # Guess artist from name (as before)
            artist = name.split(' ')[0].upper()

            concert = {
                "id": f"concert-{i}-{name}",
                "artist": artist,
                "name": name,
                "venue": venue,
                "date": date,
                "url": event_url,
                "image_url": image_url,
                "booking_url": booking_url,
                "description": "N/A", # No description from main page
                "price": "N/A" # No price from main page
            }
            concert_data.append(concert)
            concert_id_counter += 1

        with open('concerts.json', 'w', encoding='utf-8') as f:
            json.dump(concert_data, f, ensure_ascii=False, indent=4)

        print(f"Scraping complete! Found {len(concert_data)} concerts.")
        print("Data saved to concerts.json")
        return concert_data

    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {target_url}: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return [] # Return empty list on error

if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    run_scraper(query)
