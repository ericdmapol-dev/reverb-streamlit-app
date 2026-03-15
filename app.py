import streamlit as st
import requests

# خانة لإدخال API Key
API_KEY = st.text_input("Enter your Reverb API Key", type="password")

def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept-Version": "3.0"   # ضروري باش يقبل السيرفر
    }

def get_drafts(page=1):
    url = f"https://api.reverb.com/api/listings?state=draft&page={page}&per_page=10"
    r = requests.get(url, headers=get_headers())
    return r.json().get("listings", [])

def publish_draft(listing_id):
    url = f"https://api.reverb.com/api/listings/{listing_id}"
    data = {"state": "active"}
    r = requests.put(url, headers=get_headers(), json=data)
    return r.json()

st.title("Reverb Draft Manager")

if API_KEY:
    page = st.number_input("Page", min_value=1, value=1)
    drafts = get_drafts(page)

    st.subheader(f"Draft Listings (Page {page})")

    selected_ids = []
    for draft in drafts:
        title = draft.get("title") or f"{draft.get('make','')} {draft.get('model','')}"
        st.write(f"ID: {draft['id']} | {title}")
        if st.checkbox(f"Select {title}", key=draft['id']):
            selected_ids.append(draft['id'])

    if st.button("Publish Selected Drafts"):
        for listing_id in selected_ids:
            publish_draft(listing_id)
            st.success(f"Published listing ID {listing_id}!")
else:
    st.warning("⚠️ Please enter your API Key to access drafts.")
