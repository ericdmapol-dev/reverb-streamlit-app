import streamlit as st
import requests

API_KEY = "YOUR_REVERB_API_KEY"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept-Version": "3.0"
}

def get_drafts(page=1):
    url = f"https://api.reverb.com/api/listings?state=draft&page={page}&per_page=24"
    r = requests.get(url, headers=headers)
    return r.json().get("listings", [])

def publish_draft(listing_id):
    url = f"https://api.reverb.com/api/listings/{listing_id}"
    data = {"state": "active"}
    r = requests.put(url, headers=headers, json=data)
    return r.json()

st.title("Reverb Draft Manager")

page = st.number_input("Page", min_value=1, value=1)
drafts = get_drafts(page)

st.subheader(f"Draft Listings (Page {page})")

selected_ids = []
for draft in drafts:
    # نعرض العنوان أو الموديل إذا ما كاينش title
    title = draft.get("title") or f"{draft.get('make','')} {draft.get('model','')}"
    condition = draft.get("condition", "Unknown")
    st.write(f"ID: {draft['id']} | {title} | {condition}")
    if st.checkbox(f"Select {title}", key=draft['id']):
        selected_ids.append(draft['id'])

if st.button("Publish Selected Drafts"):
    for listing_id in selected_ids:
        result = publish_draft(listing_id)
        st.success(f"Published listing ID {listing_id}!")
