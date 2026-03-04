import streamlit as st
import requests

st.title("Reverb Bulk Clone Manager")

# 1. Login
token = st.text_input("🔐 دخل الـ Reverb Token ديالك:", type="password")

# 2. Bulk Clone
product_ids = st.text_area("🆔 دخل IDs أو روابط المنتجات (مفصولين بفاصلة):")

# 3. Shipping ID
shipping_id = st.text_input("🚚 دخل shipping_profile_id ديالك:")

# خيار تخفيض السعر 50%
discount = st.checkbox("💲 Clone at 50% Off")

if token and product_ids and shipping_id:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }

    ids = [pid.strip() for pid in product_ids.split(",") if pid.strip()]
    for pid in ids:
        st.markdown(f"---\n🔄 جاري نسخ المنتج: `{pid}`")

        # جلب بيانات المنتج العام
        res = requests.get(f"https://api.reverb.com/api/listings/{pid}", headers={"Accept-Version": "3.0"})
        if res.status_code != 200:
            st.error(f"❌ خطأ فـ جلب المنتج `{pid}`: {res.status_code}")
            continue

        product = res.json()

        # حساب السعر مع الخصم إذا مفعّل
        price = product.get("price", {}).get("amount", "100.00")
        if discount and price:
            try:
                price = str(float(price) / 2)
            except:
                pass

        # بناء Listing جديد
        new_listing = {
            "title": product.get("title", "منتج بدون عنوان"),
            "description": product.get("description", ""),
            "price": price,
            "currency": product.get("price", {}).get("currency", "USD"),
            "make": product.get("make", ""),
            "model": product.get("model", ""),
            "year": product.get("year", ""),
            "finish": product.get("finish", ""),
            "condition": product.get("condition", "used"),
            "shipping_profile_id": int(shipping_id)
        }

        # نسخ الصور
        photos = []
        if product.get("photos"):
            for photo in product["photos"]:
                photos.append({"url": photo["url"]})
        if photos:
            new_listing["photos"] = photos

        # إرسال POST لإنشاء المنتج الجديد
        create = requests.post("https://api.reverb.com/api/listings", headers=headers, json=new_listing)
        if create.status_code == 201:
            st.success(f"✅ المنتج `{pid}` تليستى بنجاح!")
            st.write(create.json())
        else:
            st.error(f"❌ خطأ فـ إنشاء المنتج `{pid}`: {create.status_code}")
            st.write(create.json())
