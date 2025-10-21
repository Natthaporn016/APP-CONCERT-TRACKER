# reserve.py

import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- หมายเหตุ ---
# นี่คือโค้ดตัวอย่าง คุณอาจต้องนำโค้ด Selenium เดิมของคุณมาปรับใช้
# โดยเฉพาะส่วนที่เกี่ยวกับ Logic การคลิกปุ่มต่างๆ ในเว็บ Thaiticketmajor

def main():
    # --- ส่วนที่ 1: รับข้อมูลจาก app.py ---
    # โค้ดส่วนนี้จะรับข้อมูล (ชื่อคอนเสิร์ต, โซน, อีเมล, รหัสผ่าน)
    # ที่ผู้ใช้กรอกในหน้าเว็บ มาจาก command-line arguments
    if len(sys.argv) != 5:
        print("Usage: python reserve.py <concert_name> <zone> <email> <password>")
        return

    concert_name = sys.argv[1]
    zone = sys.argv[2]
    email = sys.argv[3]
    password = sys.argv[4]
    
    # พิมพ์ Log เพื่อให้เราเห็นใน Terminal ว่าสคริปต์เริ่มทำงานแล้ว
    print("-----------------------------------------")
    print(f"ได้รับคำสั่งจองตั๋วใหม่!")
    print(f"Concert: {concert_name}")
    print(f"Zone: {zone}")
    print(f"User: {email}")
    print("-----------------------------------------")

    # --- ส่วนที่ 2: เริ่มกระบวนการจองตั๋วด้วย Selenium ---
    # คุณสามารถนำโค้ด Selenium เดิมของคุณมาวางและปรับแก้ต่อจากตรงนี้ได้เลย
    
    try:
        # เริ่มต้น Web Driver
        driver = webdriver.Chrome()
        driver.get("https://www.thaiticketmajor.com/login-ttm.php")

        # 1. กรอกข้อมูล Login ในเว็บ Thaiticketmajor
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email"))).send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]").click()

        print("Login successful. Searching for concert...")
        
        # 2. ค้นหาคอนเสิร์ต
        # (ส่วนนี้ต้องเขียน Logic เพิ่มเติมเพื่อค้นหาคอนเสิร์ตตาม `concert_name` ที่ได้รับมา)
        # ตัวอย่าง: driver.find_element(By.ID, "search-input").send_keys(concert_name)
        # ...
        
        # 3. เลือกโซน
        # (ส่วนนี้ต้องเขียน Logic เพิ่มเติมเพื่อเลือกโซนตาม `zone` ที่ได้รับมา)
        # ...

        print("Booking process simulation complete.")
        time.sleep(15) # รอ 15 วินาทีเพื่อให้เห็นผลลัพธ์

    except Exception as e:
        print(f"An error occurred during the booking process: {e}")
    finally:
        # ปิดเบราว์เซอร์เสมอ ไม่ว่าจะทำงานสำเร็จหรือล้มเหลว
        if 'driver' in locals():
            driver.quit()
        print("Booking script finished.")
        print("-----------------------------------------")


if __name__ == "__main__":
    main()

