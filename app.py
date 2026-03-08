import requests
import streamlit as st

st.set_page_config(page_title="Reverb Clone Tool", layout="centered")

st.title("Reverb Listing Cloner")

api_key = st.text_input("API Key")
shipping_profile_id = st.text_input("Shipping Profile ID")
listing_url = st.text_input("Listing URL")


def get_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/hal+json",
        "Accept": "application/hal+json"
    }


def extract_listing_id(url):
    try:
        return url.split("/item/")[1].split("-")[0]
    except:
        return None


def get_listing(api_key, listing_id):

    headers = get_headers(api_key)

    url = f"https://api.reverb.com/api/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        st.error(r.text)
        return None

    data = r.json()

    if "listing" not in data:
        st.error("Listing not found")
        return None

    return data["listing"]


def create_clone(api_key, data, shipping_profile_id):

    headers = get_headers(api_key)

    try:

        price_amount = float(data["price"]["amount"])
        currency = data["price"]["currency"]

        # تخفيض السعر 70%
        new_price = price_amount * 0.70

        payload = {
            "title": data["title"],
            "description": data["description"],
            "price": {
                "amount": str(round(new_price,2)),
                "currency": currency
            },
            "condition": {
                "uuid": data["condition"]["uuid"]
            },
            "shipping_profile_id": int(shipping_profile_id)
        }

        r = requests.post(
            "https://api.reverb.com/api/listings",
            headers=headers,
            json=payload
        )

        if r.status_code not in [200,201]:

            st.error(r.text)
            return None

        res = r.json()

        return res["listing"]["id"]

    except Exception as e:
        st.error(str(e))
        return None


def upload_image(api_key, listing_id, image_url):

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    img = requests.get(image_url)

    files = {
        "file": ("image.jpg", img.content)
    }

    url = f"https://api.reverb.com/api/listings/{listing_id}/images"

    r = requests.post(url, headers=headers, files=files)

    if r.status_code not in [200,201]:
        st.warning("Image upload failed")


def clone_images(api_key, data, listing_id):

    photos = data.get("photos", [])

    for img in photos:

        image_url = img.get("_links", {}).get("large_crop", {}).get("href")

        if image_url:
            upload_image(api_key, listing_id, image_url)


if st.button("Clone Listing"):

    if not api_key or not shipping_profile_id or not listing_url:
        st.error("Fill all fields")
        st.stop()

    listing_id = extract_listing_id(listing_url)

    if not listing_id:
        st.error("Invalid listing URL")
        st.stop()

    st.write("Fetching listing...")

    data = get_listing(api_key, listing_id)

    if data:

        st.write("Creating clone...")

        new_listing = create_clone(api_key, data, shipping_profile_id)

        if new_listing:

            st.write("Uploading images...")

            clone_images(api_key, data, new_listing)

            st.success(f"Clone created! Listing ID: {new_listing}")