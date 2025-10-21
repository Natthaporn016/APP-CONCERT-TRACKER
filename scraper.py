import requests
from bs4 import BeautifulSoup
import json
import datetime

# URL เป้าหมาย
URL = "https://www.thaiticketmajor.com/concert/"

def run_scraper():
    print("Starting scraper...")
    try:
        # ส่งคำขอไปยังเว็บไซต์
        response = requests.get(URL)
        response.raise_for_status() # เช็คว่า request สำเร็จหรือไม่

        # สกัดข้อมูล HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # ค้นหา event cards ทั้งหมด
        events = soup.select('div.event-card-item')
        
        concert_data = []
        concert_id_counter = 1

        for event in events:
            # ดึงชื่อคอนเสิร์ต
            name_tag = event.find('h3', class_='event-card-title')
            name = name_tag.text.strip() if name_tag else "N/A"

            # ดึงสถานที่
            venue_tag = event.find('p', class_='event-card-venue')
            venue = venue_tag.text.strip() if venue_tag else "N/A"

            # ดึง URL ของคอนเสิร์ต
            url_tag = event.find('a', href=True)
            event_url = url_tag['href'] if url_tag else ""
            if not event_url.startswith('http'):
                event_url = "https://www.thaiticketmajor.com" + event_url

            # หมายเหตุ: การดึงชื่อศิลปินและวันที่จากหน้าหลักทำได้ยาก
            # เราจะใช้ค่าจำลองไปก่อน และจะสมบูรณ์ขึ้นเมื่อมีฐานข้อมูล
            # ในที่นี้ เราจะพยายามเดาชื่อศิลปินจากชื่อคอนเสิร์ต
            artist = name.split(' ')[0].upper() # เดาว่าเป็นคำแรกของชื่อ

            concert = {
                "id": concert_id_counter,
                "artist": artist,
                "name": name,
                "venue": venue,
                "date": datetime.datetime.now().isoformat(), # ใช้เวลาปัจจุบันเป็น placeholder
                "url": event_url
            }
            concert_data.append(concert)
            concert_id_counter += 1

        # บันทึกข้อมูลลงไฟล์ concerts.json
        with open('concerts.json', 'w', encoding='utf-8') as f:
            json.dump(concert_data, f, ensure_ascii=False, indent=4)
        
        print(f"Scraping complete! Found {len(concert_data)} concerts.")
        print("Data saved to concerts.json")

    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {URL}: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    run_scraper()
