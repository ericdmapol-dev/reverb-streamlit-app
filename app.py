import streamlit as st
import requests
from bs4 import BeautifulSoup

st.title("🌍 Bulk Import من مواقع خارجية → Reverb")

# إدخال Token و Shipping Profile
token = st.text_input("🔐 دخل Reverb Token:", type="password")
shipping_id = st.text_input("🚚 دخل shipping_profile_id:")

# إدخال روابط المنتجات (واحد أو أكثر)
urls_input = st.text_area("📌 روابط المنتجات (واحد في كل سطر):")

if st.button("🚀 استيراد المنتجات"):
    if not token or not shipping_id or not urls_input.strip():
        st.error("❌ خاصك تدخل Token, shipping_profile_id, وروابط المنتجات.")
    else:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept-Version": "3.0",
            "Content-Type": "application/json"
        }

        urls = [u.strip() for u in urls_input.splitlines() if u.strip()]

        for url in urls:
            try:
                page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(page.content, "html.parser")

                # استخراج البيانات الأساسية (Amazon كمثال)
                title = soup.find(id="productTitle").get_text(strip=True) if soup.find(id="productTitle") else "منتج بدون عنوان"
                price = soup.find("span", {"class": "a-price-whole"}).get_text(strip=True) if soup.find("span", {"class": "a-price-whole"}) else "100.00"
                image = soup.find("img", {"id": "landingImage"})["src"] if soup.find("img", {"id": "landingImage"}) else None

                new_listing = {
                    "title": title,
                    "description": "مستورد من موقع خارجي",
                    "price": price,
                    "currency": "USD",
                    "condition": "used",
                    "shipping_profile_id": int(shipping_id),
                    "photos": [{"url": image}] if image else []
                }

                response = requests.post("https://api.reverb.com/api/listings", headers=headers, json=new_listing)

                if response.status_code == 201:
                    st.success(f"✅ المنتج من {url} تليستى بنجاح!")
                else:
                    st.error(f"❌ خطأ مع {url}: {response.status_code}")
                    st.write(response.json())

            except Exception as e:
                st.error(f"⚠️ مشكل مع الرابط {url}: {e}")
