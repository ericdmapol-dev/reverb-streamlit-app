import streamlit as st
import requests
import os

API_BASE = "https://api.reverb.com/api"

st.title("Reverb Cloner PRO MAX")


def extract_listing_id(url):
    try:
        part = url.split("/item/")[1]
        return part.split("-")[0]
    except:
        return None


def get_listing(api_key, listing_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    r = requests.get(
        f"{API_BASE}/listings/{listing_id}",
        headers=headers
    )

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


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


def download_images(listing):

    photos = listing.get("photos", [])
    paths = []

    os.makedirs("images", exist_ok=True)

    for i, photo in enumerate(photos):

        try:

            img_url = photo["_links"]["full"]["href"]

            img = requests.get(img_url).content

            path = f"images/img{i}.jpg"

            with open(path, "wb") as f:
                f.write(img)

            paths.append(path)

        except Exception as e:
            st.write("DOWNLOAD ERROR:", e)

    return paths


def create_listing(api_key, listing, shipping_profile_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    make_name, model_name = safe_make_model(listing)

    price = float(listing["price"]["amount"]) * 0.70

    payload = {

        "title": listing.get("title", "No Title"),

        "description": listing.get("description", ""),

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
        f"{API_BASE}/listings",
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
        "Accept-Version": "3.0",
        "Accept": "application/json"
    }

    st.subheader("Uploading Images Debug")

    for path in paths:

        st.write("Uploading:", path)

        try:

            # create image slot
            r = requests.post(
                f"{API_BASE}/listings/{listing_id}/images",
                headers=headers
            )

            st.write("Image slot status:", r.status_code)

            if r.status_code not in [200, 201]:
                st.write("Slot error:", r.text)
                continue

            image_data = r.json()

            upload_url = image_data["_links"]["upload"]["href"]

            st.write("Upload URL received")

            with open(path, "rb") as img:

                res = requests.put(
                    upload_url,
                    data=img,
                    headers={"Content-Type": "image/jpeg"}
                )

            st.write("Upload result:", res.status_code)

        except Exception as e:

            st.write("Upload error:", e)


api_key = st.text_input("API KEY")

shipping_profile_id = st.text_input("Shipping Profile ID")

listing_url = st.text_input("Listing URL")


if st.button("Clone Listing"):

    listing_id = extract_listing_id(listing_url)

    if not listing_id:
        st.error("Invalid URL")
        st.stop()

    st.write("Listing ID:", listing_id)

    listing = get_listing(api_key, listing_id)

    if not listing:
        st.stop()

    paths = download_images(listing)

    st.write("Downloaded Images:", paths)

    new_listing_id = create_listing(api_key, listing, shipping_profile_id)

    if not new_listing_id:
        st.stop()

    st.write("New Listing ID:", new_listing_id)

    upload_images(api_key, new_listing_id, paths)

    st.success("Clone Completed!")