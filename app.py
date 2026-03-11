import streamlit as st
import requests
import time
import os

API = "https://api.reverb.com/api"


# ---------------- HEADERS ----------------

def headers(api_key):

    return {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Accept": "application/json"
    }


# ---------------- EXTRACT LISTING ID ----------------

def extract_id(url):

    if "/item/" in url:
        return url.split("/item/")[1].split("-")[0]

    return url


# ---------------- GET LISTING ----------------

def get_listing(api_key, listing_id):

    r = requests.get(
        f"{API}/listings/{listing_id}",
        headers=headers(api_key)
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


# ---------------- DOWNLOAD IMAGES ----------------

def download_images(listing):

    os.makedirs("images", exist_ok=True)

    paths = []

    photos = listing.get("photos", [])

    for i, p in enumerate(photos):

        try:

            url = p["_links"]["full"]["href"]

            img = requests.get(url).content

            path = f"images/img{i}.jpg"

            with open(path,"wb") as f:
                f.write(img)

            paths.append(path)

            st.write("Downloaded", path)

        except:

            st.write("Image failed")

    return paths


# ---------------- EXTRACT CATEGORY ----------------

def extract_category(listing):

    categories = []

    for cat in listing.get("categories", []):
        if "uuid" in cat:
            categories.append(cat["uuid"])

    return categories


# ---------------- CREATE LISTING ----------------

def create_listing(api_key, listing, shipping):

    make = listing.get("make")
    model = listing.get("model")

    if isinstance(make, dict):
        make = make["name"]

    if isinstance(model, dict):
        model = model["name"]

    category = extract_category(listing)

    payload = {

        "title": listing["title"],

        "description": listing.get("description",""),

        "price": {
            "amount": float(listing["price"]["amount"]),
            "currency": "USD"
        },

        "condition": {
            "uuid": listing["condition"]["uuid"]
        },

        "make": make,

        "model": model,

        "finish": listing.get("finish",""),

        "year": listing.get("year",""),

        "shipping_profile_id": int(shipping),

        "category_uuids": category,

        "state": "draft"
    }

    r = requests.post(
        f"{API}/listings",
        headers=headers(api_key),
        json=payload
    )

    if r.status_code not in [200,201]:

        st.error(r.text)
        return None

    return r.json()["listing"]["id"]


# ---------------- UPLOAD IMAGES (SLOT METHOD) ----------------

def upload_images(api_key, listing_id, paths):

    h = headers(api_key)

    success = 0

    st.subheader("Uploading Images")

    for path in paths:

        st.write("Creating slot for:", path)

        slot = requests.post(
            f"{API}/listings/{listing_id}/images",
            headers=h
        )

        if slot.status_code != 201:

            st.write("Slot error:", slot.text)
            continue

        upload_url = slot.json()["upload_url"]

        st.write("Uploading image")

        with open(path,"rb") as img:

            r = requests.put(
                upload_url,
                data=img,
                headers={"Content-Type":"image/jpeg"}
            )

        if r.status_code in [200,201]:

            success += 1
            st.success("Uploaded")

        else:

            st.write("Upload failed", r.status_code)

        time.sleep(2)

    st.write("Uploaded", success, "/", len(paths))


# ---------------- STREAMLIT UI ----------------

st.title("Reverb Cloner PRO")

api_key = st.text_input("API KEY", type="password")

shipping = st.text_input("Shipping Profile ID")

url = st.text_input("Listing URL")


if st.button("CLONE LISTING"):

    listing_id = extract_id(url)

    st.write("Listing ID:", listing_id)

    listing = get_listing(api_key, listing_id)

    if not listing:
        st.stop()

    st.write("Downloading images")

    paths = download_images(listing)

    st.write("Creating listing")

    new_id = create_listing(api_key, listing, shipping)

    st.success("New Listing ID: " + str(new_id))

    st.write("Waiting 60 seconds")

    time.sleep(60)

    upload_images(api_key, new_id, paths)

    st.success("Clone completed")

    st.write("https://reverb.com/item/" + str(new_id))