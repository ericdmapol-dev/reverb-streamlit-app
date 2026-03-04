import requests
from bs4 import BeautifulSoup

# لائحة روابط المنتجات من مواقع خارجية
urls = [
    "https://www.amazon.com/dp/B08N5WRWNW",
    "https://www.amazon.com/dp/B07FZ8S74R"
]

# إعدادات Reverb
REVERB_TOKEN = "YOUR_REVERB_TOKEN"
SHIPPING_ID = 114029

headers = {
    "Authorization": f"Bearer {REVERB_TOKEN}",
    "Accept-Version": "3.0",
    "Content-Type": "application/json"
}

for url in urls:
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")

    # استخراج البيانات الأساسية
    title = soup.find(id="productTitle").get_text(strip=True) if soup.find(id="productTitle") else "منتج بدون عنوان"
    price = soup.find("span", {"class": "a-price-whole"}).get_text(strip=True) if soup.find("span", {"class": "a-price-whole"}) else "100.00"
    image = soup.find("img", {"id": "landingImage"})["src"] if soup.find("img", {"id": "landingImage"}) else None

    # بناء JSON صالح لـ Reverb
    new_listing = {
        "title": title,
        "description": "مستورد من موقع خارجي",
        "price": price,
        "currency": "USD",
        "condition": "used",
        "shipping_profile_id": SHIPPING_ID,
        "photos": [{"url": image}] if image else []
    }

    # إرسال POST للـ API ديال Reverb
    response = requests.post(
        "https://api.reverb.com/api/listings",
        headers=headers,
        json=new_listing
    )

    print(f"🔄 معالجة الرابط: {url}")
    print(response.status_code)
    print(response.json())
