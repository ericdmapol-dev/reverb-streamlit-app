import streamlit as st
import requests

API = "https://api.reverb.com/api"


# استخراج Listing ID من الرابط
def clean_id(value):

    if "reverb.com" in value:

        value = value.split("/item/")[1]
        value = value.split("-")[0]

    return value.strip()


# نشر Draft Listing
def publish_listing(api_key, listing_id):

    listing_id = clean_id(listing_id)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }

    payload = {
        "state": "live"
    }

    r = requests.put(
        f"{API}/listings/{listing_id}/state",
        headers=headers,
        json=payload
    )

    st.write("Listing ID:", listing_id)
    st.write("Status:", r.status_code)

    if r.status_code == 200:

        st.success("Listing Published")

        st.write("Live Link:")
        st.write("https://reverb.com/item/" + listing_id)

    else:

        st.error(r.text)


# واجهة التطبيق
st.title("Reverb Draft Publisher")

api_key = st.text_input("API KEY", type="password")

listing_id = st.text_input("Draft Listing ID or URL")

if st.button("Publish Listing"):

    publish_listing(api_key, listing_id)