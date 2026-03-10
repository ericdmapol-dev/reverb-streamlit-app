import streamlit as st
import requests
import os
import time
from pathlib import Path

API_BASE = "https://api.reverb.com/api"

# ================= HEADERS =================

def headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Accept": "application/json"
    }

# ================= EXTRACT LISTING ID =================

def extract_listing_id(url):

    if "/item/" in url:
        return url.split("/item/")[1].split("-")[0]

    return None


# ================= GET LISTING =================

def get_listing(api_key, listing_id):

    r = requests.get(
        f"{API_BASE}/listings/{listing_id}",
        headers=headers(api_key)
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


# ================= DOWNLOAD IMAGES =================

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

            st.write("Downloaded", path)

        except:
            st.warning("image error")

    return paths


# ================= CREATE LISTING =================

def create_listing(api_key, listing, shipping_profile_id):

    make = listing["make"]
    model = listing["model"]

    if isinstance(make, dict):
        make = make["name"]

    if isinstance(model, dict):
        model = model["name"]

    payload = {

        "title": listing["title"],

        "description": listing["description"],

        "price": {
            "amount": listing["price"]["amount"],
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
        headers=headers(api_key),
        json=payload
    )

    if r.status_code not in [200,201]:
        st.error(r.text)
        return None

    return r.json()["listing"]["id"]


# ================= REQUEST IMAGE SLOT =================

def request_image_slot(api_key, listing_id):

    r = requests.post(
        f"{API_BASE}/listings/{listing_id}/images",
        headers=headers(api_key)
    )

    if r.status_code != 201:
        st.error("Slot error")
        st.write(r.text)
        return None

    return r.json()


# ================= UPLOAD IMAGE =================

def upload_image(upload_url, path):

    with open(path,"rb") as img:

        r = requests.put(
            upload_url,
            data=img,
            headers={"Content-Type":"image/jpeg"}
        )

    return r.status_code in [200,201]


# ================= UPLOAD IMAGES =================

def upload_images(api_key, listing_id, paths):

    success = 0

    for p in paths:

        st.write("Uploading", p)

        slot = request_image_slot(api_key, listing_id)

        if not slot:
            continue

        upload_url = slot["upload_url"]

        ok = upload_image(upload_url, p)

        if ok:
            success += 1
            st.success("Uploaded")
        else:
            st.error("Upload failed")

        time.sleep(2)

    st.write("Uploaded", success, "/", len(paths))


# ================= PUBLISH =================

def publish_listing(api_key, listing_id):

    r = requests.put(
        f"{API_BASE}/listings/{listing_id}/publish",
        headers=headers(api_key)
    )

    return r.status_code in [200,201,204]


# ================= STREAMLIT UI =================

st.title("🎸 Reverb Cloner PRO MAX")

api_key = st.text_input("API Key", type="password")

shipping_profile_id = st.text_input("Shipping Profile ID")

url = st.text_input("Listing URL")

if st.button("Clone Listing"):

    listing_id = extract_listing_id(url)

    st.write("Listing ID:", listing_id)

    listing = get_listing(api_key, listing_id)

    if not listing:
        st.stop()

    st.write("Downloading images")

    paths = download_images(listing)

    st.write(paths)

    st.write("Creating listing")

    new_id = create_listing(api_key, listing, shipping_profile_id)

    st.success("New Listing ID: " + str(new_id))

    st.write("Waiting 25 seconds")

    time.sleep(25)

    upload_images(api_key, new_id, paths)

    publish_listing(api_key, new_id)

    st.success("Clone Completed")

    st.markdown(f"https://reverb.com/item/{new_id}")