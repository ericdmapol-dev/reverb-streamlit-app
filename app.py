import requests
import streamlit as st

st.title("Reverb Listing Cloner")

api_key = st.text_input("API Key")
shipping_profile_id = st.text_input("Shipping Profile ID")
listing_url = st.text_input("Listing URL")


def get_listing(api_key, listing_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }

    url = f"https://api.reverb.com/api/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        return r.json()["listing"]

    else:
        st.error(r.text)
        return None


def create_clone(api_key, data, shipping_profile_id):

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept-Version": "3.0"
    }

    try:

        price_amount = float(data["price"]["amount"])
        currency = data["price"]["currency"]

        # تخفيض السعر 70%
        price_amount = price_amount * 0.70

        payload = {
            "title": data["title"],
            "description": data["description"],
            "price": {
                "amount": price_amount,
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

        if r.status_code == 201:

            listing_id = r.json()["listing"]["id"]

            return listing_id

        else:

            st.error(r.text)
            return None

    except Exception as e:

        st.error(str(e))
        return None


def upload_image(api_key, listing_id, image_url):

    try:

        img = requests.get(image_url)

        files = {
            "file": ("image.jpg", img.content)
        }

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        url = f"https://api.reverb.com/api/listings/{listing_id}/images"

        r = requests.post(url, headers=headers, files=files)

        return r.status_code

    except Exception as e:

        st.error(str(e))


def clone_images(api_key, data, new_listing_id):

    try:

        images = data.get("photos", [])

        for img in images:

            image_url = img.get("_links", {}).get("large_crop", {}).get("href")

            if image_url:
                upload_image(api_key, new_listing_id, image_url)

    except Exception as e:

        st.error(str(e))


if st.button("Clone Listing"):

    try:

        listing_id = listing_url.split("/")[-1]

        data = get_listing(api_key, listing_id)

        if data:

            new_listing_id = create_clone(api_key, data, shipping_profile_id)

            if new_listing_id:

                clone_images(api_key, data, new_listing_id)

                st.success("Listing cloned successfully with images!")

    except Exception as e:

        st.error(str(e))