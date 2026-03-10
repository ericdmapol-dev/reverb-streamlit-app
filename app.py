import streamlit as st
import requests
import time
import os

API_BASE = "https://api.reverb.com/api"


# ---------------- HEADERS ----------------

def get_headers(api_key):

    return {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Accept": "application/json"
    }


# ---------------- EXTRACT LISTING ID ----------------

def extract_listing_id(url):

    if "/item/" in url:
        return url.split("/item/")[1].split("-")[0]

    return url.strip()


# ---------------- GET LISTING ----------------

def get_listing(api_key, listing_id):

    r = requests.get(
        f"{API_BASE}/listings/{listing_id}",
        headers=get_headers(api_key)
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


# ---------------- DOWNLOAD IMAGES ----------------

def download_images(listing):

    photos = listing.get("photos", [])

    if not photos:
        st.warning("No photos found")
        return []

    os.makedirs("images", exist_ok=True)

    paths = []

    for i, photo in enumerate(photos):

        try:

            url = photo["_links"]["full"]["href"]

            img = requests.get(url).content

            path = f"images/img{i}.jpg"

            with open(path, "wb") as f:
                f.write(img)

            st.success(f"Downloaded {path}")

            paths.append(path)

        except:

            st.warning("Failed to download image")

    return paths


# ---------------- CREATE LISTING ----------------

def create_listing(api_key, listing, shipping_profile):

    make = listing.get("make")
    model = listing.get("model")

    if isinstance(make, dict):
        make = make.get("name")

    if isinstance(model, dict):
        model = model.get("name")

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

        headers=get_headers(api_key),

        json=payload
    )

    if r.status_code not in [200, 201]:

        st.error(r.text)
        return None

    new_id = r.json()["listing"]["id"]

    return new_id


# ---------------- UPLOAD IMAGES ----------------

def upload_images(api_key, listing_id, paths):

    headers = get_headers(api_key)

    success = 0

    st.subheader("Uploading Images")

    for path in paths:

        st.write("Uploading", path)

        try:

            with open(path, "rb") as img:

                files = {
                    "file": ("image.jpg", img, "image/jpeg")
                }

                r = requests.post(
                    f"https://api.reverb.com/api/listings/{listing_id}/images",
                    headers=headers,
                    files=files
                )

            st.write("Status:", r.status_code)

            if r.status_code in [200, 201]:

                success += 1
                st.success("Uploaded")

            else:

                st.error(r.text)

        except Exception as e:

            st.error(e)

        time.sleep(2)

    st.write("Uploaded", success, "/", len(paths))


# ---------------- PUBLISH ----------------

def publish_listing(api_key, listing_id):

    r = requests.put(
        f"{API_BASE}/listings/{listing_id}/publish",
        headers=get_headers(api_key)
    )

    if r.status_code in [200, 201, 204]:

        st.success("Listing Published")

    else:

        st.warning("Publish failed")


# ---------------- STREAMLIT UI ----------------

st.title("Reverb Listing Cloner")


api_key = st.text_input("API KEY", type="password")

shipping_profile = st.text_input("Shipping Profile ID")

listing_url = st.text_input("Listing URL")


if st.button("CLONE LISTING"):

    listing_id = extract_listing_id(listing_url)

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

    st.write("Waiting 40 seconds for listing to be ready")

    time.sleep(40)

    upload_images(api_key, new_id, paths)

    publish_listing(api_key, new_id)

    st.success("Clone Completed")

    st.markdown(f"https://reverb.com/item/{new_id}")