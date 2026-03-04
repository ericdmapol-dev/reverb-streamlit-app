import streamlit as st
import requests

st.title("📦 إعادة نشر منتجات تباعو إلى حسابي على Reverb")

# إدخال الـ Token ديالك
token = st.text_input("🔐 دخل الـ Reverb Token ديالك:", type="password")

# إدخال shipping_profile_id
shipping_id = st.text_input("🚚 دخل shipping_profile_id ديالك:")

# إدخال تفاصيل المنتج يدوياً (مثلاً من صفحة تباع)
title = st.text_input("📌 عنوان المنتج:", "Epiphone Custom Bull Chandler 1984")
description = st.text_area("📝 وصف المنتج:", "نسخة طبق الأصل من منتج تباع سابقاً")
price = st.text_input("💲 السعر:", "2500.00")
currency = st.text_input("💱 العملة:", "USD")
make = st.text_input("🏭 الشركة المصنعة:", "Epiphone")
model = st.text_input("🎸 الموديل:", "Custom Bull Chandler")
year = st.text_input("📅 السنة:", "1984")
finish = st.text_input("🎨 اللون/التشطيب:", "Sunburst")
condition = st.selectbox("⚡ الحالة:", ["new", "mint", "excellent", "good", "fair", "poor"], index=3)

photos_input = st.text_area("🖼️ روابط الصور (مفصولين بفاصلة):", "https://link-to-photo1.jpg, https://link-to-photo2.jpg")

if token and shipping_id and title and price:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }

    photos = [{"url": url.strip()} for url in photos_input.split(",") if url.strip()]

    new_listing = {
        "title": title,
        "description": description,
        "price": price,
        "currency": currency,
        "make": make,
        "model": model,
        "year": year,
        "finish": finish,
        "condition": condition,
        "shipping_profile_id": int(shipping_id),
        "photos": photos
    }

    response = requests.post(
        "https://api.reverb.com/api/listings",
        headers=headers,
        json=new_listing
    )

    if response.status_code == 201:
        st.success("✅ المنتج تليستى بنجاح فكونطك!")
        st.write(response.json())
    else:
        st.error(f"❌ خطأ فـ إنشاء المنتج: {response.status_code}")
        st.write(response.json())
