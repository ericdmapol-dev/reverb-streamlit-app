import streamlit as st
import requests
import os
import time
from pathlib import Path

API_BASE = "https://api.reverb.com/api"


# ---------------- HEADERS ----------------

def headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }


# ---------------- EXTRACT LISTING ID ----------------

def get_listing_id(url):

    if "/item/" in url:
        return url.split("/item/")[1].split("-")[0]

    return url


# ---------------- GET LISTING ----------------

def get_listing(api_key, listing_id):

    r = requests.get(
        f"{API_BASE}/listings/{listing_id}",
        headers=headers(api_key)
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


# ---------------- DOWNLOAD IMAGES ----------------

def download_images(listing):

    Path("images").mkdir(exist_ok=True)

    photos = listing.get("photos", [])

    paths = []

    for i, photo in enumerate(photos):

        try:

            url = photo["_links"]["full"]["href"]

            img = requests.get(url).content

            path = f"images/img{i}.jpg"

            with open(path, "wb") as f:
                f.write(img)

            paths.append(path)

            st.success(f"Downloaded {path}")

        except:

            st.warning("Image skipped")

    return paths


# ---------------- CREATE LISTING ----------------

def create_listing(api_key, listing, shipping_profile):

    make = listing.get("make")
    model = listing.get("model")

    if isinstance(make, dict):
        make = make["name"]

    if isinstance(model, dict):
        model = model["name"]

    payload = {

        "title": listing["title"],

        "description": listing.get("description", ""),

        "price": {
            "amount": float(listing["price"]["amount"]),
            "currency": "USD"
        },

        "condition": {
            "uuid": listing["condition"]["uuid"]
        },

        "make": make,
        "model": model,

        "finish": listing.get("finish", ""),

        "year": listing.get("year", ""),

        "shipping_profile_id": int(shipping_profile),

        "state": "draft"
    }

    r = requests.post(

        f"{API_BASE}/listings",

        headers=headers(api_key),

        json=payload
    )

    if r.status_code not in [200, 201]:

        st.error(r.text)
        return None

    new_id = r.json()["listing"]["id"]

    return new_id


# ---------------- UPLOAD IMAGES ----------------

def upload_images(api_key, listing_id, paths):

    success = 0

    for path in paths:

        st.write("Uploading", path)

        with open(path, "rb") as img:

            files = {
                "photo": img
            }

            r = requests.post(

                f"{API_BASE}/listings/{listing_id}/photos",

                headers=headers(api_key),

                files=files
            )

        st.write("Status:", r.status_code)

        if r.status_code in [200, 201]:

            success += 1
            st.success("Uploaded")

        else:

            st.error(r.text)

        time.sleep(1)

    st.write("Uploaded", success, "/", len(paths))


# ---------------- PUBLISH ----------------

def publish_listing(api_key, listing_id):

    r = requests.put(

        f"{API_BASE}/listings/{listing_id}/publish",

        headers=headers(api_key)

    )

    if r.status_code in [200, 201, 204]:

        st.success("Listing published")

    else:

        st.warning("Publish failed")


# ---------------- STREAMLIT ----------------

st.title("Reverb Listing Cloner")

api_key = st.text_input("API KEY", type="password")

shipping_profile = st.text_input("Shipping Profile ID")

listing_url = st.text_input("Listing URL")


if st.button("CLONE LISTING"):

    listing_id = get_listing_id(listing_url)

    st.write("Listing ID:", listing_id)

    listing = get_listing(api_key, listing_id)

    if not listing:
        st.stop()

    st.write("Downloading images")

    paths = download_images(listing)

    st.write(paths)

    st.write("Creating listing")

    new_id = create_listing(api_key, listing, shipping_profile)

    st.success(f"New Listing ID: {new_id}")

    st.write("Waiting 25 seconds")

    time.sleep(25)

    upload_images(api_key, new_id, paths)

    publish_listing(api_key, new_id)

    st.success("Clone Completed")

    st.markdown(f"https://reverb.com/item/{new_id}")