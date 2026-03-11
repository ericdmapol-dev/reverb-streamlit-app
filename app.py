import streamlit as st
import requests
import time
import os

API = "https://api.reverb.com/api"


def headers(api):
    return {
        "Authorization": f"Bearer {api}",
        "Accept-Version": "3.0"
    }


def extract_id(url):

    if "/item/" in url:
        return url.split("/item/")[1].split("-")[0]

    return url


def get_listing(api, listing_id):

    r = requests.get(
        f"{API}/listings/{listing_id}",
        headers=headers(api)
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


def download_images(listing):

    os.makedirs("images", exist_ok=True)

    paths = []

    photos = listing.get("photos", [])

    for i, p in enumerate(photos):

        url = p["_links"]["full"]["href"]

        img = requests.get(url).content

        path = f"images/img{i}.jpg"

        with open(path,"wb") as f:
            f.write(img)

        paths.append(path)

        st.write("Downloaded", path)

    return paths


def extract_category(listing):

    cats = listing.get("categories", [])

    if not cats:
        return []

    return [cats[-1]["uuid"]]


def create_listing(api, listing, shipping):

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
        headers=headers(api),
        json=payload
    )

    if r.status_code not in [200,201]:

        st.error(r.text)
        return None

    return r.json()["listing"]["id"]


def upload_images(api, listing_id, paths):

    success = 0

    for path in paths:

        st.write("Uploading", path)

        with open(path,"rb") as img:

            files = {
                "file": ("image.jpg", img, "image/jpeg")
            }

            r = requests.post(
                f"{API}/listings/{listing_id}/images",
                headers=headers(api),
                files=files
            )

        st.write("Status:", r.status_code)

        if r.status_code in [200,201]:

            success += 1
            st.success("Uploaded")

        else:

            st.write(r.text)

        time.sleep(2)

    st.write("Uploaded", success, "/", len(paths))


st.title("Reverb Cloner")


api_key = st.text_input("API KEY", type="password")

shipping = st.text_input("Shipping Profile ID")

url = st.text_input("Listing URL")


if st.button("CLONE"):

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