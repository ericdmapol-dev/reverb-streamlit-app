import streamlit as st
import requests

API_KEY = "YOUR_REVERB_API_KEY"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Get drafts
def get_drafts():
    url = "https://api.reverb.com/api/listings?state=draft"
    r = requests.get(url, headers=headers)
    return r.json().get("listings", [])

# Publish draft
def publish_draft(listing_id):
    url = f"https://api.reverb.com/api/listings/{listing_id}"
    data = {"state": "active"}
    r = requests.put(url, headers=headers, json=data)
    return r.json()

st.title("Reverb Draft Manager")

drafts = get_drafts()

st.subheader("Draft Listings")

selected_ids = []
for draft in drafts:
    if st.checkbox(f"{draft['title']} - {draft['condition']}", key=draft['id']):
        selected_ids.append(draft['id'])

if st.button("Publish Selected Drafts"):
    for listing_id in selected_ids:
        result = publish_draft(listing_id)
        st.success(f"Published listing ID {listing_id}!")
