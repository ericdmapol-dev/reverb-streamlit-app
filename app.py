import streamlit as st
import requests
from bs4 import BeautifulSoup
import os

st.title("Reverb Listing Cloner PRO")

api_key = st.text_input("API Key")
shipping_profile_id = st.text_input("Shipping Profile ID")
listing_url = st.text_input("Listing URL")


def extract_listing_id(url):
    try:
        part = url.split("/item/")[1]
        listing_id = part.split("-")[0]
        return listing_id
    except:
        return None


def get_listing(api_key, listing_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }

    url = f"https://api.reverb.com/api/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


def create_listing(api_key, listing, shipping_profile_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }

    price = float(listing["price"]["amount"]) * 0.70

    # معالجة make و model إذا كانوا غير موجودين
    make = listing.get("make")
    model = listing.get("model")

    make_name = make["name"] if make else "Unknown"
    model_name = model if model else "Unknown"

    payload = {
        "title": listing.get("title","No Title"),
        "description": listing.get("description",""),

        "price": {
            "amount": price,
            "currency": listing["price"]["currency"]
        },

        "condition": {
            "uuid": listing["condition"]["uuid"]
        },

        "make": make_name,
        "model": model_name,

        "shipping_profile_id": int(shipping_profile_id)
    }

    r = requests.post(
        "https://api.reverb.com/api/listings",
        headers=headers,
        json=payload
    )

    data = r.json()

    if "listing" not in data:
        st.error(data)
        return None

    return data["listing"]["id"]


def download_images_from_page(listing_url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(listing_url, headers=headers)

    soup = BeautifulSoup(r.text, "html.parser")

    image_urls = []
    paths = []

    for img in soup.find_all("img"):

        src = img.get("src")

        if src and "reverb-res.cloudinary.com" in src:

            if src not in image_urls:
                image_urls.append(src)

    os.makedirs("images", exist_ok=True)

    for i, url in enumerate(image_urls):

        try:

            img_data = requests.get(url).content

            path = f"images/img{i}.jpg"

            with open(path, "wb") as f:
                f.write(img_data)

            paths.append(path)

        except:
            pass

    return paths


def upload_images(api_key, listing_id, paths):

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    for path in paths:

        try:

            with open(path, "rb") as f:

                files = {
                    "photo": f
                }

                url = f"https://api.reverb.com/api/listings/{listing_id}/photos"

                r = requests.post(url, headers=headers, files=files)

                print(r.text)

        except:
            pass


if st.button("Clone Listing"):

    listing_id = extract_listing_id(listing_url)

    if not listing_id:
        st.error("Invalid URL")
        st.stop()

    listing = get_listing(api_key, listing_id)

    if listing:

        new_listing_id = create_listing(api_key, listing, shipping_profile_id)

        if new_listing_id:

            paths = download_images_from_page(listing_url)

            if paths:
                upload_images(api_key, new_listing_id, paths)

            st.success(f"Clone Complete! Listing ID: {new_listing_id}")