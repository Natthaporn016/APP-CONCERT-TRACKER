# CONCERT TRACKER

แอปพลิเคชันสำหรับติดตามคอนเสิร์ตและกิจกรรมดนตรีต่างๆ ในประเทศไทย โดยเน้นการเชื่อมโยงกับประสบการณ์ทางดนตรีส่วนตัวของคุณผ่าน Spotify

## คุณสมบัติหลัก

*   **ค้นหาคอนเสิร์ต:** ค้นหาคอนเสิร์ตล่าสุดจาก [ThaiTicketMajor](https://www.thaiticketmajor.com/)
*   **เชื่อมต่อ Spotify:**
    *   แสดงศิลปินที่คุณฟังบ่อยจาก Spotify
    *   ค้นหาคอนเสิร์ตของศิลปินที่คุณชื่นชอบโดยตรง

*   **ค้นหาตามศิลปิน:** ค้นหาคอนเสิร์ตของศิลปินที่คุณต้องการโดยเฉพาะ
*   **ข้อมูลคอนเสิร์ตสำรอง:** หากการดึงข้อมูลสดจากเว็บไซต์มีปัญหา ระบบจะใช้ข้อมูลคอนเสิร์ตที่บันทึกไว้ในเครื่อง

## การติดตั้งและรันแอปพลิเคชัน

### 1. โคลน Repository

```bash
git clone https://github.com/Natthaporn016/APP-CONCERT-TRACKER.git
cd APP-CONCERT-TRACKER
```

### 2. สร้างและเปิดใช้งาน Virtual Environment

```bash
python -m venv venv
# สำหรับ Windows
.\venv\Scripts\activate
# สำหรับ macOS/Linux
source venv/bin/activate
```

### 3. ติดตั้ง Dependencies

```bash
pip install Flask python-dotenv requests beautifulsoup4 spotipy google-auth-oauthlib google-api-python-client
```

### 4. ตั้งค่า Environment Variables

สร้างไฟล์ `.env` ใน root directory ของโปรเจกต์ และเพิ่มข้อมูลต่อไปนี้:

```
FLASK_SECRET_KEY="your_flask_secret_key"
SPOTIPY_CLIENT_ID="your_spotify_client_id"
SPOTIPY_CLIENT_SECRET="your_spotify_client_secret"
SPOTIPY_REDIRECT_URI="http://127.0.0.1:5000/callback" # หรือ URL ที่คุณตั้งค่าไว้
```
*   **FLASK_SECRET_KEY**: คีย์ลับสำหรับ Flask session (สามารถสร้างสตริงสุ่มขึ้นมาได้)

*   **Spotify API Credentials**:
    *   ไปที่ [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
    *   สร้างแอปพลิเคชันใหม่
    *   แก้ไขการตั้งค่า (Edit Settings) และเพิ่ม `http://127.0.0.1:5000/callback` เป็น Redirect URI
    *   คัดลอก Client ID และ Client Secret มาใส่ในไฟล์ `.env`

### 5. รัน Scraper (ไม่บังคับ)

หากต้องการดึงข้อมูลคอนเสิร์ตล่าสุดและบันทึกลงใน `concerts.json` ด้วยตนเอง:

```bash
python scraper.py
```

### 6. รันแอปพลิเคชัน

```bash
flask run
# หรือ
python app.py
```

แอปพลิเคชันจะทำงานที่ `http://127.0.0.1:5000/`

## โครงสร้างโปรเจกต์

```
.
├── app.py              # ไฟล์หลักของ Flask application
├── concerts.json       # ข้อมูลคอนเสิร์ตสำรอง
├── .env                # ไฟล์สำหรับเก็บ Environment Variables (ไม่ควร commit ขึ้น Git)
├── reserve.py          # (อาจจะเป็นส่วนที่ยังไม่ได้ใช้งานเต็มที่ หรือสำหรับฟังก์ชันการจอง)
├── scraper.py          # สคริปต์สำหรับดึงข้อมูลคอนเสิร์ตจาก ThaiTicketMajor
├── static/             # ไฟล์ CSS และอื่นๆ สำหรับ frontend
│   └── style.css
└── templates/          # ไฟล์ HTML templates
    └── index.html
```
