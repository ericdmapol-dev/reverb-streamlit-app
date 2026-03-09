import streamlit as st
import requests
import os

st.title("Reverb Cloner PRO MAX")

API_BASE = "https://api.reverb.com/api"


# استخراج ID من الرابط
def extract_listing_id(url):
    try:
        part = url.split("/item/")[1]
        return part.split("-")[0]
    except:
        return None


# جلب بيانات Listing
def get_listing(api_key, listing_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }

    url = f"{API_BASE}/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        st.error(r.text)
        return None

    return r.json()


# معالجة make / model
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


# تحميل الصور
def download_images(listing):

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

        except Exception as e:
            print("DOWNLOAD ERROR", e)

    return paths


# إنشاء Listing جديد
def create_listing(api_key, listing, shipping_profile_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
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


# رفع الصور
def upload_images(api_key, listing_id, paths):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }

    for path in paths:

        try:

            # إنشاء photo slot
            r = requests.post(
                f"{API_BASE}/listings/{listing_id}/photos",
                headers=headers
            )

            if r.status_code != 201:
                print("PHOTO SLOT ERROR", r.text)
                continue

            data = r.json()

            upload_url = data["upload_url"]

            with open(path, "rb") as f:

                upload_headers = {
                    "Content-Type": "image/jpeg"
                }

                res = requests.put(
                    upload_url,
                    data=f,
                    headers=upload_headers
                )

                print("UPLOAD STATUS", res.status_code)

        except Exception as e:
            print("UPLOAD ERROR", e)


# واجهة التطبيق
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