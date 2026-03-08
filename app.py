import streamlit as st
import requests
import re
import time
import random

st.title("Reverb Bulk Clone Manager")

token = st.text_input("Reverb Token", type="password")
urls = st.text_area("Product URLs or IDs (one per line)")
shipping_profile_id = st.text_input("Shipping Profile ID")
discount = st.checkbox("Clone at 50% Off")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/hal+json",
    "Accept-Version": "3.0",
    "Content-Type": "application/json"
}

def extract_id(text):

    match = re.search(r'item/(\d+)', text)

    if match:
        return match.group(1)

    digits = re.findall(r'\d+', text)

    if digits:
        return digits[0]

    return None


def get_listing(listing_id):

    url = f"https://api.reverb.com/api/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        st.error(f"API Error {r.status_code}")
        st.text(r.text)
        return None

    try:
        return r.json()
    except:
        st.error("Invalid JSON response")
        return None


def create_clone(data):

    try:

        price = float(data["price"]["amount"])

        if discount:
            price = price * 0.5

        payload = {
            "title": data["title"],
            "description": data["description"],
            "price": price,
            "shipping_profile_id": shipping_profile_id,
            "condition": data["condition"]["slug"]
        }

        r = requests.post(
            "https://api.reverb.com/api/listings",
            headers=headers,
            json=payload
        )

        if r.status_code not in [200,201]:
            st.error(f"Clone Error {r.status_code}")
            st.text(r.text)

        return r.status_code

    except Exception as e:
        st.error(str(e))
        return None


if st.button("Start Clone"):

    lines = urls.split("\n")

    progress = st.progress(0)

    for i, line in enumerate(lines):

        listing_id = extract_id(line)

        if not listing_id:
            st.warning(f"Invalid link: {line}")
            continue

        data = get_listing(listing_id)

        if not data:
            continue

        result = create_clone(data)

        st.write(f"Cloned {listing_id} → Status {result}")

        progress.progress((i + 1) / len(lines))

        time.sleep(random.randint(2,5))