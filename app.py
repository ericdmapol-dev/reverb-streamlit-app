import streamlit as st
import requests

API = "https://api.reverb.com/api"


def clean_id(value):

    if "reverb.com" in value:
        return value.split("/item/")[1].split("-")[0]

    return value


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

    r = requests.patch(
        f"{API}/listings/{listing_id}",
        headers=headers,
        json=payload
    )

    st.write("Status:", r.status_code)

    if r.status_code == 200:

        st.success("Listing Published")

        st.write("https://reverb.com/item/" + listing_id)

    else:

        st.error(r.text)


st.title("Reverb Draft Publisher")

api_key = st.text_input("API KEY", type="password")

listing_id = st.text_input("Draft Listing ID")

if st.button("Publish"):

    publish_listing(api_key, listing_id)