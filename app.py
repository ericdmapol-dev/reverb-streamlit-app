import streamlit as st
import requests
import os
import time
from pathlib import Path

API_BASE = "https://api.reverb.com/api"

# ---------- HEADERS ----------
def get_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Accept": "application/json"
    }

# ---------- EXTRACT LISTING ID ----------
def extract_listing_id(url):

    if "/item/" in url:
        return url.split("/item/")[1].split("-")[0]

    return None


# ---------- GET LISTING ----------
def get_listing(api_key, listing_id):

    r = requests.get(
        f"{API_BASE}/listings/{listing_id}",
        headers=get_headers(api_key)
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


# ---------- DOWNLOAD IMAGES ----------
def download_images(listing):

    photos = listing.get("photos", [])

    if not photos:
        return []

    Path("images").mkdir(exist_ok=True)

    paths = []

    for i, photo in enumerate(photos):

        try:

            img_url = photo["_links"]["full"]["href"]

            img = requests.get(img_url).content

            path = f"images/img{i}.jpg"

            with open(path, "wb") as f:
                f.write(img)

            paths.append(path)

            st.write(f"✅ Downloaded image {i+1}")

        except:
            st.warning("image error")

    return paths


# ---------- EXTRACT MAKE MODEL ----------
def extract_make_model(listing):

    make = listing.get("make")
    model = listing.get("model")

    make_name = make["name"] if isinstance(make, dict) else make
    model_name = model["name"] if isinstance(model, dict) else model

    return make_name, model_name


# ---------- CREATE LISTING ----------
def create_listing(api_key, listing, shipping_profile_id):

    make, model = extract_make_model(listing)

    price = float(listing["price"]["amount"])

    payload = {

        "title": listing["title"],

        "description": listing.get("description",""),

        "price": {
            "amount": price,
            "currency": "USD"
        },

        "condition": {
            "uuid": listing["condition"]["uuid"]
        },

        "make": make,
        "model": model,

        "finish": listing.get("finish",""),
        "year": listing.get("year",""),

        "shipping_profile_id": int(shipping_profile_id),

        "state": "draft"
    }

    r = requests.post(
        f"{API_BASE}/listings",
        headers=get_headers(api_key),
        json=payload
    )

    if r.status_code not in [200,201]:
        st.error(r.text)
        return None

    data = r.json()

    return data["listing"]["id"]


# ---------- UPLOAD IMAGES ----------
def upload_images(api_key, listing_id, paths):

    headers = get_headers(api_key)

    success = 0

    st.subheader("Uploading Images")

    for p in paths:

        st.write("Uploading:", p)

        with open(p,"rb") as img:

            files = {
                "file": img
            }

            r = requests.post(

                f"https://api.reverb.com/api/listings/{listing_id}/cloudinary_photos",

                headers=headers,
                files=files
            )

        st.write("Status:", r.status_code)

        if r.status_code in [200,201]:

            success += 1

    st.write(f"Uploaded {success}/{len(paths)} images")

    return success


# ---------- PUBLISH ----------
def publish_listing(api_key, listing_id):

    r = requests.put(

        f"{API_BASE}/listings/{listing_id}/publish",

        headers=get_headers(api_key)
    )

    return r.status_code in [200,201,204]


# ---------- UI ----------
st.set_page_config(page_title="Reverb Cloner PRO", page_icon="🎸")

st.title("🎸 Reverb Cloner PRO")

api_key = st.text_input("API Key", type="password")

shipping_profile_id = st.text_input("Shipping Profile ID")

url = st.text_input("Listing URL")

if st.button("Clone Listing"):

    listing_id = extract_listing_id(url)

    st.write("Listing ID:", listing_id)

    listing = get_listing(api_key, listing_id)

    if not listing:
        st.stop()

    st.write("Downloading images...")

    paths = download_images(listing)

    st.write(paths)

    st.write("Creating listing...")

    new_listing_id = create_listing(api_key, listing, shipping_profile_id)

    st.success(f"New Listing ID: {new_listing_id}")

    st.write("Waiting 20 seconds...")

    time.sleep(20)

    upload_images(api_key, new_listing_id, paths)

    publish_listing(api_key, new_listing_id)

    st.success("Clone Completed!")

    st.markdown(f"https://reverb.com/item/{new_listing_id}")