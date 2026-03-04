import streamlit as st
import requests

st.title("منتج عام من Reverb")

# خانة لإدخال ID ديال المنتج
listing_id = st.text_input("دخل ID ديال المنتج (مثلاً 94566420):")

if listing_id:
    url = f"https://api.reverb.com/api/listings/{listing_id}"
    response = requests.get(url, headers={"Accept-Version": "3.0"})
    
    if response.status_code == 200:
        data = response.json()
        st.write("📩 رد API:", data)

        st.subheader("📦 تفاصيل المنتج:")
        st.write(f"**{data['title']}**")
        st.write(f"💲 {data['price']['amount']} {data['price']['currency']}")
        if data.get("photos"):
            for photo in data["photos"][:3]:  # نعرض أول 3 صور فقط
                st.image(photo["url"], width=250)
    else:
        st.error(f"❌ خطأ: {response.status_code}")
