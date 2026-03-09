import streamlit as st
import requests
import os

st.title("Reverb Cloner PRO")

api_key = st.text_input("API KEY")
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


def download_images_from_api(listing):

    photos = listing.get("photos", [])

    paths = []

    os.makedirs("images", exist_ok=True)

    for i, photo in enumerate(photos):

        try:

            url = photo["_links"]["full"]["href"]

            img = requests.get(url).content

            path = f"images/img{i}.jpg"

            with open(path, "wb") as f:
                f.write(img)

            paths.append(path)

        except:
            pass

    return paths


def safe_make_model(listing):

    make = listing.get("make")
    model = listing.get("model")

    if isinstance(make, dict):
        make_name = make.get("name", "Unknown")
    elif isinstance(make, str):
        make_name = make
    else:
        make_name = "Unknown"

    if isinstance(model, str):
        model_name = model
    else:
        model_name = "Unknown"

    return make_name, model_name


def create_listing(api_key, listing, shipping_profile_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }

    price = float(listing["price"]["amount"]) * 0.70

    make_name, model_name = safe_make_model(listing)

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


def upload_images(api_key, listing_id, paths):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }

    for path in paths:

        try:

            # create photo slot
            r = requests.post(
                f"https://api.reverb.com/api/listings/{listing_id}/photos",
                headers=headers
            )

            upload_url = r.json()["upload_url"]

            with open(path,"rb") as f:

                requests.put(upload_url,data=f)

        except:
            pass


if st.button("Clone Listing"):

    listing_id = extract_listing_id(listing_url)

    listing = get_listing(api_key, listing_id)

    if listing:

        paths = download_images_from_api(listing)

        st.write(paths)

        new_listing_id = create_listing(api_key, listing, shipping_profile_id)

        if new_listing_id:

            upload_images(api_key, new_listing_id, paths)

            st.success(f"Clone Done: {new_listing_id}")