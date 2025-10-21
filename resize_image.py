import requests
from PIL import Image
from io import BytesIO

# URL รูปภาพโปสเตอร์คอนเสิร์ต BIBI ที่เคยใช้ในขั้นตอนก่อนหน้า
image_url = "http://googleusercontent.com/image_collection/image_retrieval/2883509636573418193_0"
output_filename = "BIBI_resized.jpg"
target_width = 400 # กำหนดความกว้างใหม่เป็น 400 พิกเซล

try:
    # 1. ดาวน์โหลดรูปภาพ
    print(f"กำลังดาวน์โหลดรูปภาพจาก: {image_url}")
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()

    # 2. เปิดและปรับขนาดรูปภาพ
    img = Image.open(BytesIO(response.content))

    original_width, original_height = img.size
    new_height = int(original_height * (target_width / original_width))

    resized_img = img.resize((target_width, new_height))

    # 3. บันทึกรูปภาพที่ปรับขนาดแล้ว
    resized_img.save(output_filename, "JPEG")
    
    print(f"เสร็จสมบูรณ์! รูปภาพถูกปรับขนาดเป็น {target_width}x{new_height} พิกเซล และบันทึกเป็นไฟล์ {output_filename}")
    print("กรุณาอัปโหลดไฟล์นี้ไปยังเซิร์ฟเวอร์ของคุณ (เช่น โฟลเดอร์ /static/images) เพื่อให้แอปพลิเคชัน Flask สามารถเข้าถึงได้")

except requests.exceptions.RequestException as e:
    print(f"เกิดข้อผิดพลาดในการดาวน์โหลดรูปภาพ: {e}")
except Exception as e:
    print(f"เกิดข้อผิดพลาดในการประมวลผลรูปภาพ: {e}")