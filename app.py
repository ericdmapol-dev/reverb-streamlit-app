import streamlit as st
import requests
import json

API_KEY = "YOUR_REVERB_API_KEY"
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Load drafts
def load_drafts():
    try:
        with open("drafts.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_drafts(drafts):
    with open("drafts.json", "w") as f:
        json.dump(drafts, f)

def publish_to_reverb(draft):
    data = {
        "title": draft["title"],
        "description": draft["description"],
        "price": draft["price"],
        "currency": "USD",
        "condition": "used",
        "photos": [{"photo_url": draft["photo_url"]}]
    }
    response = requests.post("https://api.reverb.com/api/listings", headers=headers, json=data)
    return response.json()

st.title("Reverb Draft Manager")

drafts = load_drafts()

# Form to add draft
with st.form("new_draft"):
    title = st.text_input("Title")
    description = st.text_area("Description")
    price = st.text_input("Price")
    photo_url = st.text_input("Photo URL (direct link)")
    submitted = st.form_submit_button("Save Draft")
    if submitted:
        drafts.append({"title": title, "description": description, "price": price, "photo_url": photo_url, "status": "draft"})
        save_drafts(drafts)
        st.success("Draft saved!")

# Show drafts
st.subheader("Draft Listings")
for i, draft in enumerate(drafts):
    st.write(f"{i+1}. {draft['title']} - {draft['status']}")
    if st.button(f"Publish {draft['title']}", key=i):
        result = publish_to_reverb(draft)
        draft["status"] = "published"
        save_drafts(drafts)
        st.success(f"Published {draft['title']} to Reverb!")
