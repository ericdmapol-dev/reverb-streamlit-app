import streamlit as st
import requests

st.title("🗂️ Reverb Bulk Clone Manager")

# إدخال Token
token = st.text_input("🔒 أدخل Reverb Token الخاص بك:", type="password")

# إدخال روابط المنتجات (IDs أو URLs)
urls_input = st.text_area("🆔 أدخل IDs أو روابط المنتجات (واحد في كل سطر):")

# إدخال shipping_profile_id
shipping_id = st.text_input("🚚 أدخل shipping_profile_id الخاص بك:")

# خيار تخفيض السعر (مثلاً 50%)
discount = st.checkbox("☑️ 💲 Clone at 50% Off")

if st.button("🚀 بدء النسخ"):
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
            st.write(f"🗂️ جاري نسخ المنتج: {url}")
            try:
                # هنا خاصك تجيب بيانات المنتج الأصلي (مثلاً عبر API أو scraping)
                # مؤقتاً نخلي مثال بسيط
                new_listing = {
                    "title": "نسخة من المنتج الأصلي",
                    "description": "تم نسخه من رابط خارجي",
                    "price": "100.00",
                    "currency": "USD",
                    "condition": "used",
                    "shipping_profile_id": int(shipping_id),
                    "photos": [{"url": "https://i.imgur.com/example.jpg"}]
                }

                # إذا كان خيار التخفيض مفعّل
                if discount:
                    new_listing["price"] = str(float(new_listing["price"]) * 0.5)

                response = requests.post("https://api.reverb.com/api/listings",
                                         headers=headers,
                                         json=new_listing)

                if response.status_code == 201:
                    st.success(f"✅ المنتج من {url} تليستى بنجاح!")
                else:
                    st.error(f"❌ خطأ مع {url}: {response.status_code}")
                    st.write(response.json())

            except Exception as e:
                st.error(f"⚠️ مشكل مع الرابط {url}: {e}")
