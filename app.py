import streamlit as st
import requests
import os
import time

API = "https://api.reverb.com/api"


def headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }


def clean_id(value):

    if "reverb.com" in value:
        value = value.split("/item/")[1]
        value = value.split("-")[0]

    return value.strip()


def get_listing(api_key, listing_id):

    r = requests.get(
        f"{API}/listings/{listing_id}",
        headers=headers(api_key)
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


def download_images(listing):

    os.makedirs("images", exist_ok=True)

    paths = []

    photos = listing.get("photos", [])

    st.write("Downloading images")

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


def get_categories(listing):

    cats = []

    for c in listing.get("categories", []):

        if "uuid" in c:
            cats.append(c["uuid"])

    return cats


def create_listing(api_key, listing):

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

        "category_uuids": get_categories(listing),

        "state": "live"
    }

    st.write("Creating listing")

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


def upload_images(api_key, listing_id, paths):

    h = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }

    st.write("Uploading Images")

    for path in paths:

        st.write("Uploading", path)

        with open(path, "rb") as img:

            files = {"file": img}

            r = requests.post(
                f"{API}/listings/{listing_id}/images",
                headers=h,
                files=files
            )

        st.write("Status:", r.status_code)

        if r.status_code not in [200, 201]:
            st.write(r.text)

        time.sleep(2)


st.title("Reverb Clone Bot")


api_key = st.text_input("API KEY", type="password")

listing_url = st.text_input("Listing URL or ID")


if st.button("CLONE LISTING"):

    listing_id = clean_id(listing_url)

    st.write("Listing ID:", listing_id)

    listing = get_listing(api_key, listing_id)

    if not listing:
        st.stop()

    paths = download_images(listing)

    new_id = create_listing(api_key, listing)

    if not new_id:
        st.stop()

    st.write("Waiting 60 seconds")

    time.sleep(60)

    upload_images(api_key, new_id, paths)

    st.success("Clone Completed")

    st.write("https://reverb.com/item/" + str(new_id))