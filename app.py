import streamlit as st
import requests
from bs4 import BeautifulSoup

st.title("🌍 Multi-Site Import → Reverb مع رفع الصور")

token = st.text_input("4a045b7e8d29aff1b6c630982d1206f6d17c56edbf529c52cbd08e81494e0d78")
shipping_id = st.text_input("114105")

urls_input = st.text_area("📌 https://www.ebay.com/itm/366022048648?_skw=GUTAR&itmmeta=01KJWPJCAF61AE8J8ZABPXT273&hash=item55389d3b88:g:cWEAAeSwGSZpJ9Mh&itmprp=enc%3AAQALAAAA4GfYFPkwiKCW4ZNSs2u11xAiVUxMAi7c3BYmqJhJ6phqGZ7zNHWwGI5nbyByvfRk89dQuB6ksJGY%2FKWdMHre30dDZw0kgWwvSYGQbUl82F4jrR2ppc3wdI%2BaU8ghy2jEb%2BVCNS0if1G06pQrfK2cWJmAFnkehv1qYufFZSoUSdEVaAzaH0nmhyfHlFVdNeENWl%2FJcB8XKzE%2B3cXlNsAczbl%2FAhOKVzzXCZQM%2Fin9eyaHjqWBVxuWeub1978gS81NwtfjHOi8yBxJ44chsvnuorg21XtqXP7d33KVXlkB9Y17%7Ctkp%3ABk9SR4bGyZaXZw):")
uploaded_files = st.file_uploader("🖼️ رفع صور إضافية (اختياري):", type=["jpg","png"], accept_multiple_files=True)

def scrape_amazon(url):
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    title = soup.find(id="productTitle").get_text(strip=True) if soup.find(id="productTitle") else "منتج بدون عنوان"
    price = soup.find("span", {"class": "a-price-whole"}).get_text(strip=True) if soup.find("span", {"class": "a-price-whole"}) else "100.00"
    image = soup.find("img", {"id": "landingImage"})["src"] if soup.find("img", {"id": "landingImage"}) else None
    return title, price, image

def scrape_ebay(url):
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    title = soup.find("h1", {"class": "x-item-title__mainTitle"}).get_text(strip=True) if soup.find("h1", {"class": "x-item-title__mainTitle"}) else "منتج بدون عنوان"
    price = soup.find("span", {"itemprop": "price"}).get_text(strip=True) if soup.find("span", {"itemprop": "price"}) else "100.00"
    image = soup.find("img", {"id": "icImg"})["src"] if soup.find("img", {"id": "icImg"}) else None
    return title, price, image

def scrape_aliexpress(url):
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(page.content, "html.parser")
    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "منتج بدون عنوان"
    price = soup.find("div", {"class": "product-price-value"}).get_text(strip=True) if soup.find("div", {"class": "product-price-value"}) else "100.00"
    image = soup.find("img", {"class": "magnifier-image"})["src"] if soup.find("img", {"class": "magnifier-image"}) else None
    return title, price, image

if st.button("🚀 استيراد المنتجات"):
    if not token or not shipping_id or not urls_input.strip():
        st.error("4a045b7e8d29aff1b6c630982d1206f6d17c56edbf529c52cbd08e81494e0d78, 114105, https://www.ebay.com/itm/366022048648?_skw=GUTAR&itmmeta=01KJWPJCAF61AE8J8ZABPXT273&hash=item55389d3b88:g:cWEAAeSwGSZpJ9Mh&itmprp=enc%3AAQALAAAA4GfYFPkwiKCW4ZNSs2u11xAiVUxMAi7c3BYmqJhJ6phqGZ7zNHWwGI5nbyByvfRk89dQuB6ksJGY%2FKWdMHre30dDZw0kgWwvSYGQbUl82F4jrR2ppc3wdI%2BaU8ghy2jEb%2BVCNS0if1G06pQrfK2cWJmAFnkehv1qYufFZSoUSdEVaAzaH0nmhyfHlFVdNeENWl%2FJcB8XKzE%2B3cXlNsAczbl%2FAhOKVzzXCZQM%2Fin9eyaHjqWBVxuWeub1978gS81NwtfjHOi8yBxJ44chsvnuorg21XtqXP7d33KVXlkB9Y17%7Ctkp%3ABk9SR4bGyZaXZw.")
    else:
        headers = {
            "Authorization": f"Bearer {4a045b7e8d29aff1b6c630982d1206f6d17c56edbf529c52cbd08e81494e0d78}",
            "Accept-Version": "3.0",
            "Content-Type": "application/json"
        }

        urls = [u.strip() for u in urls_input.splitlines() if u.strip()]

        for url in urls:
            try:
                if "amazon" in url:
                    title, price, image = scrape_amazon(url)
                elif "ebay" in url:
                    title, price, image = scrape_ebay(url)
                elif "aliexpress" in url:
                    title, price, image = scrape_aliexpress(url)
                else:
                    st.warning(f"⚠️ الموقع غير مدعوم حالياً: {url}")
                    continue

                # الصور: إذا ما كانش رابط صالح، نستعمل الصور المرفوعة
                photos = []
                if image:
                    photos.append({"" https://drive.google.com/file/d/13i6ah45K-UTkvc8-KgUVhSDkHPSRx5yf/view?usp=drive_link"": image})
                if uploaded_files:
                    for file in uploaded_files:
                        # هنا خاصك ترفع الصور لخدمة خارجية (مثلاً Imgur API) باش تولّد روابط مباشرة
                        # مؤقتاً نخليها Placeholder
                        photos.append({"url": "https://i.imgur.com/example.jpg"})

                new_listing = {
                    "title": title,
                    "description": "مستورد من موقع خارجي",
                    "price": price,
                    "currency": "USD",
                    "condition": "used",
                    "shipping_profile_id": int(shipping_id),
                    "photos": photos
                }

                response = requests.post("https://api.reverb.com/api/listings", headers=headers, json=new_listing)

                if response.status_code == 201:
                    st.success(f"✅ المنتج من {url} تليستى بنجاح!")
                else:
                    st.error(f"❌ خطأ مع {url}: {response.status_code}")
                    st.write(response.json())

            except Exception as e:
                st.error(f"⚠️ مشكل مع الرابط {url}: {e}")
