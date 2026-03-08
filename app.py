import streamlit as st
import requests
import re
import time
import random
import os

st.title("Reverb Bulk Clone Manager FULL")

token = st.text_input("Reverb Token", type="password")
urls = st.text_area("Product URLs or IDs (one per line)")
shipping_profile_id = st.text_input("Shipping Profile ID")

discount = st.checkbox("Clone at 70% Price")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/hal+json",
    "Accept-Version": "3.0",
    "Content-Type": "application/json"
}

os.makedirs("temp_images", exist_ok=True)

# استخراج ID
def extract_id(text):

    match = re.search(r'item/(\d+)', text)

    if match:
        return match.group(1)

    digits = re.findall(r'\d+', text)

    if digits:
        return digits[0]

    return None


# جلب بيانات المنتج
def get_listing(listing_id):

    url = f"https://api.reverb.com/api/listings/{listing_id}"

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        st.error(f"API Error {r.status_code}")
        st.text(r.text)
        return None

    try:
        return r.json()
    except:
        st.error("Invalid JSON response")
        return None


# استخراج روابط الصور
def get_images(data):

    images = []

    try:
        for img in data["_embedded"]["images"]:
            images.append(img["_links"]["full"]["href"])
    except:
        pass

    return images


# تحميل الصور محليًا
def download_images(listing_id, image_urls):

    local_files = []

    for idx, url in enumerate(image_urls):

        try:

            r = requests.get(url)

            if r.status_code == 200:

                filename = f"temp_images/{listing_id}_{idx}.jpg"

                with open(filename, "wb") as f:
                    f.write(r.content)

                local_files.append(filename)

        except:
            continue

    return local_files


# إنشاء clone
def create_clone(data):

    try:

        price_amount = float(data["price"]["amount"])
        currency = data["price"]["currency"]

        if discount:
            price_amount = price_amount * 0.7

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

        if r.status_code in [200,201]:

            response = r.json()

            if "listing_id" in response:
                return response["listing_id"]

            if "id" in response:
                return response["id"]

            return None

        else:

            st.error(f"Clone Error {r.status_code}")
            st.text(r.text)
            return None

    except Exception as e:

        st.error(str(e))
        return None


# رفع الصور
def upload_local_images(listing_id, local_files):

    url = f"https://api.reverb.com/api/listings/{listing_id}/images"

    for file_path in local_files:

        try:

            with open(file_path, "rb") as f:

                files = {"image[file]": (os.path.basename(file_path), f)}

                r = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    files=files
                )

                if r.status_code not in [200,201]:
                    st.warning("Image upload failed")

        except:
            continue

        time.sleep(1)


# تشغيل clone
if st.button("Start Clone"):

    if not token:
        st.error("Enter Reverb Token")
        st.stop()

    lines = urls.split("\n")

    total = len(lines)

    progress = st.progress(0)

    for i, line in enumerate(lines):

        listing_id = extract_id(line)

        if not listing_id:

            st.warning(f"Invalid input: {line}")
            continue

        data = get_listing(listing_id)

        if not data:
            continue

        image_urls = get_images(data)

        new_listing = create_clone(data)

        if new_listing:

            local_files = download_images(new_listing, image_urls)

            upload_local_images(new_listing, local_files)

            st.success(f"Cloned {listing_id} → New Listing {new_listing}")

        progress.progress((i + 1) / total)

        time.sleep(random.randint(2,5))