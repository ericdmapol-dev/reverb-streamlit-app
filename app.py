import requests
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://reverb.com/"
}

LISTING_IDS = [
    "94447315",
    "94215509",
    "93460650"
]


def fetch_listing(listing_id):
    url = f"https://reverb.com/api/listings/{listing_id}"

    try:
        response = requests.get(url, headers=HEADERS)

        print(f"\nProcessing: {listing_id}")
        print("API Status:", response.status_code)

        if response.status_code == 200:
            data = response.json()

            title = data.get("title")
            price = data.get("price", {}).get("amount")
            currency = data.get("price", {}).get("currency")

            print("Title:", title)
            print("Price:", price, currency)

        else:
            print("Failed to fetch", listing_id)

    except Exception as e:
        print("Error:", e)


print("Starting Reverb Listings Fetcher...\n")

for listing_id in LISTING_IDS:
    fetch_listing(listing_id)
    time.sleep(2)