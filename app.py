import streamlit as st
import requests
import re
import time

st.title("Reverb Bulk Clone Manager")

token = st.text_input("Reverb Token", type="password")
urls = st.text_area("Product URLs or IDs (one per line)")
shipping_profile_id = st.text_input("Shipping Profile ID")
discount = st.checkbox("Clone at 50% Off")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/hal+json"
}

def extract_id(url):
    match = re.search(r'/item/(\d+)', url)
    if match:
        return match.group(1)
    return url

def get_listing(listing_id):
    url = f"https://api.reverb.com/api/listings/{listing_id}"
    r = requests.get(url, headers=headers)
    return r.json()

def create_clone(data):

    price = float(data["price"]["amount"])

    if discount:
        price = price * 0.5

    clone = {
        "title": data["title"],
        "description": data["description"],
        "price": price,
        "shipping_profile_id": shipping_profile_id,
        "condition": data["condition"]["slug"]
    }

    r = requests.post(
        "https://api.reverb.com/api/listings",
        headers=headers,
        json=clone
    )

    return r.status_code

if st.button("Start Clone"):

    lines = urls.split("\n")

    for line in lines:

        listing_id = extract_id(line)

        data = get_listing(listing_id)

        result = create_clone(data)

        st.write(f"Cloned {listing_id} → Status {result}")

        time.sleep(3)