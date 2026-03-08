import requests
import streamlit as st

API_KEY = "6297e5ad5f8128d94abb778e49ed921a89a21eae42cedb3b4df7e07ad77ea624"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept-Version": "3.0"
}

shipping_profile_id = 114202


def get_listing(listing_id):

    url = f"https://api.reverb.com/api/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code == 200:
        return r.json()["listing"]

    else:
        st.error("Error getting listing")
        return None


def create_clone(data):

    try:

        price_amount = float(data["price"]["amount"])
        currency = data["price"]["currency"]

        # تخفيض 70%
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


def upload_image(listing_id, image_url):

    try:

        img = requests.get(image_url)

        files = {
            "file": ("image.jpg", img.content)
        }

        url = f"https://api.reverb.com/api/listings/{listing_id}/images"

        r = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}"}, files=files)

        return r.status_code

    except Exception as e:

        st.error(str(e))


def clone_images(data, new_listing_id):

    try:

        images = data.get("photos", [])

        for img in images:

            image_url = img.get("_links", {}).get("large_crop", {}).get("href")

            if image_url:
                upload_image(new_listing_id, image_url)

    except Exception as e:

        st.error(str(e))


st.title("Reverb Listing Cloner")

listing_url = st.text_input("Listing URL")

if st.button("Clone Listing"):

    try:

        listing_id = listing_url.split("/")[-1]

        data = get_listing(listing_id)

        if data:

            new_listing_id = create_clone(data)

            if new_listing_id:

                clone_images(data, new_listing_id)

                st.success("Listing cloned with images!")

    except Exception as e:

        st.error(str(e))