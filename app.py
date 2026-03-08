import streamlit as st
import requests

st.title("Reverb Listing Cloner")

api_key = st.text_input("API Key")
shipping_profile_id = st.text_input("Shipping Profile ID")
listing_url = st.text_input("Listing URL")


def extract_id(url):
    try:
        return url.split("/item/")[1].split("-")[0]
    except:
        return None


def get_listing(api_key, listing_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }

    url = f"https://api.reverb.com/api/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


def create_listing(api_key, listing, shipping_profile_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }

    price = float(listing["price"]["amount"]) * 0.70

    payload = {
        "title": listing["title"],
        "description": listing["description"],
        "price": {
            "amount": price,
            "currency": listing["price"]["currency"]
        },
        "condition": {
            "uuid": listing["condition"]["uuid"]
        },
        "shipping_profile_id": int(shipping_profile_id)
    }

    r = requests.post(
        "https://api.reverb.com/api/listings",
        headers=headers,
        json=payload
    )

    if r.status_code not in [200, 201]:
        st.error(r.text)
        return None

    return r.json()["id"]


if st.button("Clone Listing"):

    listing_id = extract_id(listing_url)

    if not listing_id:
        st.error("Invalid URL")
        st.stop()

    listing = get_listing(api_key, listing_id)

    if listing:

        new_id = create_listing(api_key, listing, shipping_profile_id)

        if new_id:
            st.success(f"Listing cloned! ID: {new_id}")