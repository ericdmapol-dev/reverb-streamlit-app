import streamlit as st
import requests

st.title("منتجاتي على Reverb")

# خانة لإدخال الـ Token
token = st.text_input("دخل الـ Reverb Token ديالك:", type="password")

if token:
    headers = {
        "Authorization": f"Bearerf3d720af60f2e6e7ef362acbbd9bc715b33afa3d519e9cb234074654856469b7",
        "Accept-Version": "3.0"
    }

    # طلب المنتجات من Reverb
    response = requests.get("https://api.reverb.com/api/my/listings", headers=headers)

    if response.status_code == 200:
        listings = response.json()["_embedded"]["listings"]

        st.subheader("📦 المنتجات ديالك:")
        for item in listings:
            st.write(f"**{item['title']}**")
            st.write(f"💲 {item['price']['amount']} {item['price']['currency']}")
            if item.get("photos"):
                for photo in item["photos"][:2]:  # نعرض أول صورتين فقط
                    st.image(photo["url"], width=200)
            st.markdown("---")
    else:
        st.error("ما قدرش يجيب المنتجات من Reverb. تأكد من الـ Token.")
