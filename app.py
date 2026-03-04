import streamlit as st
import requests

st.title("نسخ منتج عام إلى حسابي على Reverb")

# إدخال الـ Token ديالك
token = st.text_input("دخل الـ Reverb Token ديالك:", type="password")

# إدخال ID ديال المنتج العام
product_id = st.text_input("دخل ID ديال المنتج العام:")

if token and product_id:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }

    # 1. نجيب بيانات المنتج العام
    response = requests.get(f"https://api.reverb.com/api/listings/{product_id}")
    if response.status_code == 200:
        product = response.json()
        st.write("📩 بيانات المنتج العام:", product)

        # 2. نبني Listing جديد فكونط ديالي بنفس البيانات
        new_listing = {
            "title": product.get("title", "منتج بدون عنوان"),
            "description": f"نسخة من منتج عام: {product.get('title', '')}",
            "price": product.get("price", {}).get("amount", "100.00"),
            "currency": product.get("price", {}).get("currency", "USD"),
            "make": product.get("make", ""),
            "model": product.get("model", ""),
            "year": product.get("year", ""),
            "finish": product.get("finish", ""),
            "condition": "used",   # خاصك تحدد الحالة
            "shipping_profile_id": 123456  # بدّلها بالـ ID ديال الشحن من حسابك
        }

        # 3. نرسل الطلب لإنشاء المنتج الجديد
        create_response = requests.post(
            "https://api.reverb.com/api/listings",
            headers=headers,
            json=new_listing
        )

        if create_response.status_code == 201:
            st.success("✅ المنتج تليستى بنجاح فكونطك!")
            st.write(create_response.json())
        else:
            st.error(f"❌ ما قدرش يخلق المنتج: {create_response.status_code}")
            st.write(create_response.json())
    else:
        st.error(f"❌ خطأ فـ جلب المنتج العام: {response.status_code}")
