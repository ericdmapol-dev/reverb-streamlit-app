import streamlit as st
import requests
import re
import time
import random

st.set_page_config(page_title="Reverb Bulk Clone Manager")

st.title("Reverb Bulk Clone Manager")

token = st.text_input("Reverb Token", type="password")
urls = st.text_area("Product URLs or IDs (one per line)")
shipping_profile_id = st.text_input("Shipping Profile ID")
discount = st.checkbox("Clone at 50% Off")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/hal+json; version=3",
    "Content-Type": "application/json"
}

def extract_id(text):
    match = re.search(r'/item/(\d+)', text)
    if match:
        return match.group(1)
    return text.strip()

def get_listing(listing_id):

    try:

        url = f"https://api.reverb.com/api/listings/{listing_id}/show"

        r = requests.get(url, headers=headers)

        st.write("API Status:", r.status_code)

        if r.status_code != 200:
            return None

        return r.json()

    except Exception as e:
        st.error(e)
        return None


def create_clone(data):

    try:

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

    except Exception as e:
        st.error(e)
        return "error"


if st.button("Start Clone"):

    if token == "":
        st.error("Enter Reverb Token")
        st.stop()

    lines = [l for l in urls.split("\n") if l.strip() != ""]

    total = len(lines)

    if total == 0:
        st.error("Add at least one listing URL")
        st.stop()

    progress = st.progress(0)

    for i, line in enumerate(lines):

        listing_id = extract_id(line)

        st.write("Processing:", listing_id)

        data = get_listing(listing_id)

        if not data:
            st.error(f"Failed to fetch {listing_id}")
            continue

        result = create_clone(data)

        if result == 201 or result == 200:
            st.success(f"Cloned {listing_id}")
        else:
            st.error(f"Clone error {listing_id}")

        progress.progress((i + 1) / total)

        time.sleep(random.randint(2,5))