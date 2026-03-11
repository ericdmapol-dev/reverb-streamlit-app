import streamlit as st
import requests
import os
import time

API = "https://api.reverb.com/api"


# -------- HEADERS --------

def headers(api_key):

    return {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }


# -------- EXTRACT LISTING ID --------

def extract_id(url):

    if "/item/" in url:
        return url.split("/item/")[1].split("-")[0]

    return url


# -------- GET LISTING --------

def get_listing(api_key, listing_id):

    r = requests.get(
        f"{API}/listings/{listing_id}",
        headers=headers(api_key)
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


# -------- DOWNLOAD IMAGES --------

def download_images(listing):

    st.write("Downloading images")

    os.makedirs("images", exist_ok=True)

    paths = []

    photos = listing.get("photos", [])

    for i, p in enumerate(photos):

        try:

            url = p["_links"]["full"]["href"]

            img = requests.get(url).content

            path = f"images/img{i}.jpg"

            with open(path, "wb") as f:
                f.write(img)

            st.write("Downloaded", path)

            paths.append(path)

        except:

            st.write("Image failed")

    return paths


# -------- GET CATEGORY --------

def get_category(listing):

    categories = []

    for c in listing.get("categories", []):

        if "uuid" in c:
            categories.append(c["uuid"])

    return categories


# -------- CREATE LISTING --------

def create_listing(api_key, listing, shipping):

    st.write("Creating listing")

    categories = get_category(listing)

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

        "make": listing.get("make", ""),

        "model": listing.get("model", ""),

        "finish": listing.get("finish", ""),

        "year": listing.get("year", ""),

        "category_uuids": categories,

        "shipping_profile_id": int(shipping),

        "state": "draft"
    }

    r = requests.post(
        f"{API}/listings",
        headers=headers(api_key),
        json=payload
    )

    if r.status_code not in [200, 201]:

        st.error(r.text)
        return None

    new_id = r.json()["listing"]["id"]

    st.success("New Listing ID: " + str(new_id))

    return new_id


# -------- UPLOAD IMAGES --------

def upload_images(api_key, listing_id, paths):

    st.subheader("Uploading Images")

    h = headers(api_key)

    success = 0

    for path in paths:

        st.write("Uploading", path)

        try:

            with open(path, "rb") as img:

                files = {
                    "image": img
                }

                r = requests.post(
                    f"{API}/listings/{listing_id}/images",
                    headers=h,
                    files=files
                )

            st.write("Status:", r.status_code)

            if r.status_code in [200, 201]:

                success += 1
                st.success("Uploaded")

            else:

                st.write("Upload error:", r.text)

        except Exception as e:

            st.write("Error:", e)

        time.sleep(2)

    st.write("Uploaded", success, "/", len(paths))


# -------- UI --------

st.title("Reverb Listing Cloner")

api_key = st.text_input("API KEY", type="password")

shipping = st.text_input("Shipping Profile ID")

url = st.text_input("Listing URL")


if st.button("CLONE LISTING"):

    listing_id = extract_id(url)

    st.write("Listing ID:", listing_id)

    listing = get_listing(api_key, listing_id)

    if not listing:
        st.stop()

    paths = download_images(listing)

    new_id = create_listing(api_key, listing, shipping)

    if not new_id:
        st.stop()

    st.write("Waiting 90 seconds")

    time.sleep(90)

    upload_images(api_key, new_id, paths)

    st.success("Clone Completed")

    st.write("https://reverb.com/item/" + str(new_id))