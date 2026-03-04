import streamlit as st
import requests

st.title("منتجاتي على Reverb")

# خانة لإدخال الـ Token
token = st.text_input("دخل الـ Reverb Token ديالك:", type="password")

if token:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Version": "3.0"
    }

    # طلب المنتجات من Reverb
    response = requests.get("https://api.reverb.com/api/my/listings", headers=headers)

    if response.status_code == 200:
        data = response.json()
        st.write("📩 رد API:", data)  # باش تشوف الرد الحقيقي

        if "_embedded" in data and "listings" in data["_embedded"]:
            listings = data["_embedded"]["listings"]

            st.subheader("📦 المنتجات ديالك:")
            for item in listings:
                st.write(f"**{item['title']}**")
                st.write(f"💲 {item['price']['amount']} {item['price']['currency']}")
                if item.get("photos"):
                    for photo in item["photos"][:2]:  # نعرض أول صورتين فقط
                        st.image(photo["url"], width=200)
                st.markdown("---")
        else:
            st.warning("⚠️ الرد ما فيهش منتجات أو ناقص صلاحيات.")
    else:
        st.error(f"❌ خطأ: {response.status_code} - ما قدرش يجيب المنتجات. تأكد من الـ Token والصلاحيات.")
