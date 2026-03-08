import streamlit as st
import requests

st.title("Reverb Listing Cloner")

api_key = st.text_input("Reverb API Key")
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
        "Authorization": api_key,
        "Accept-Version": "3.0"
    }

    url = f"https://api.reverb.com/api/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        st.error(f"API Error: {r.text}")
        return None

    return r.json()


def create_clone(api_key, listing, shipping_profile_id):

    headers = {
        "Authorization": api_key,
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }

    try:

        price = float(listing["price"]["amount"])
        currency = listing["price"]["currency"]

        # تخفيض السعر 70%
        price = price * 0.70

        payload = {
            "title": listing["title"],
            "description": listing["description"],
            "price": {
                "amount": price,
                "currency": currency
            },
            "condition": {
                "uuid": listing["condition"]["uuid"]
            },
            "shipping_profile_id": int(shipping_profile_id)
        }

        r = requests.post(
            "https://api.reverb.com/api/listings",
            headers=headers,
            json=payload
        )

        if r.status_code not in [200, 201]:
            st.error(r.text)
            return None

        return r.json()["id"]

    except Exception as e:
        st.error(str(e))
        return None


def upload_images(api_key, listing_id, listing):

    headers = {
        "Authorization": api_key
    }

    photos = listing.get("photos", [])

    for photo in photos:

        try:

            img_url = photo["_links"]["large_crop"]["href"]

            img = requests.get(img_url)

            files = {
                "file": ("image.jpg", img.content)
            }

            url = f"https://api.reverb.com/api/listings/{listing_id}/images"

            requests.post(url, headers=headers, files=files)

        except:
            pass


if st.button("Clone Listing"):

    if not api_key or not shipping_profile_id or not listing_url:
        st.error("Fill all fields")
        st.stop()

    listing_id = extract_listing_id(listing_url)

    if not listing_id:
        st.error("Invalid Listing URL")
        st.stop()

    listing = get_listing(api_key, listing_id)

    if listing:

        new_listing_id = create_clone(api_key, listing, shipping_profile_id)

        if new_listing_id:

            upload_images(api_key, new_listing_id, listing)

            st.success("Listing cloned successfully!")