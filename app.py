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
for draft in drafts:
    st.write(f"{draft['title']} - {draft['condition']}")
    if st.button(f"Publish {draft['title']}", key=draft['id']):
        result = publish_draft(draft['id'])
        st.success(f"Published {draft['title']}!")
