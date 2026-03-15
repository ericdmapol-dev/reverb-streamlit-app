import streamlit as st
import requests

API_KEY = "YOUR_REVERB_API_KEY"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Get drafts from Reverb
def get_drafts():
    response = requests.get("https://api.reverb.com/api/listings?state=draft", headers=headers)
    return response.json().get("listings", [])

# Publish draft
def publish_draft(listing_id):
    data = {"state": "active"}
    response = requests.put(f"https://api.reverb.com/api/listings/{listing_id}", headers=headers, json=data)
    return response.json()

st.title("Reverb Draft Manager")

drafts = get_drafts()

st.subheader("Draft Listings")
for draft in drafts:
    st.write(f"{draft['title']} - {draft['condition']}")
    if st.button(f"Publish {draft['title']}", key=draft['id']):
        result = publish_draft(draft['id'])
        st.success(f"Published {draft['title']}!")
