import streamlit as st
import requests
import json

# Page configuration
st.set_page_config(page_title="Reverb Draft Manager", page_icon="📋", layout="centered")
st.title("📋 Reverb Draft Manager - Simple & Direct")
st.markdown("---")

API_BASE = "https://api.reverb.com/api"

def get_my_drafts(api_key):
    """Fetch all drafts from my account"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }
    
    try:
        # Get my listings (drafts)
        response = requests.get(
            f"{API_BASE}/my/listings",
            headers=headers,
            params={"state": "draft", "per_page": 50},
            timeout=15
        )
        
        if response.status_code != 200:
            return None, f"Error: {response.status_code}"
        
        data = response.json()
        
        # Extract listings from response
        if "listings" in data:
            return data["listings"], None
        elif isinstance(data, list):
            return data, None
        else:
            return [], None
            
    except Exception as e:
        return None, str(e)

def publish_draft(api_key, listing_id):
    """Publish a draft listing"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.put(
            f"{API_BASE}/listings/{listing_id}/publish",
            headers=headers,
            timeout=15
        )
        
        if response.status_code in [200, 201, 204]:
            return True, "Published successfully!"
        else:
            return False, f"Error: {response.status_code}"
            
    except Exception as e:
        return False, str(e)

def delete_draft(api_key, listing_id):
    """Delete a draft listing"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(
            f"{API_BASE}/listings/{listing_id}",
            headers=headers,
            timeout=15
        )
        
        if response.status_code in [200, 201, 204]:
            return True, "Deleted successfully!"
        else:
            return False, f"Error: {response.status_code}"
            
    except Exception as e:
        return False, str(e)

# Main interface
st.header("🔑 Connect to Reverb")

# API Key input
api_key = st.text_input("Enter your Reverb API Key", type="password", help="Your API key must have write permissions")

if api_key:
    # Button to fetch drafts
    if st.button("📋 Load My Drafts", type="primary", use_container_width=True):
        with st.spinner("Loading your drafts..."):
            drafts, error = get_my_drafts(api_key)
            
            if error:
                st.error(f"Failed to load drafts: {error}")
            elif drafts:
                st.success(f"✅ Found {len(drafts)} drafts in your account")
                
                # Store in session state
                st.session_state.drafts = drafts
            else:
                st.info("No drafts found in your account")
    
    # Display drafts if they exist in session state
    if 'drafts' in st.session_state and st.session_state.drafts:
        st.markdown("---")
        st.header(f"📋 Your Drafts ({len(st.session_state.drafts)})")
        
        for draft in st.session_state.drafts:
            # Extract listing info
            listing_id = draft.get('id')
            title = draft.get('title', 'Untitled')
            make = draft.get('make', 'Unknown')
            model = draft.get('model', 'Unknown')
            price = draft.get('price', {}).get('amount', '0')
            currency = draft.get('price', {}).get('currency', 'USD')
            photos = draft.get('photos', [])
            photo_count = len(photos)
            
            # Display each draft in a card
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{title}**")
                    st.write(f"📌 ID: `{listing_id}`")
                    st.write(f"🏷️ {make} - {model}")
                    st.write(f"💰 {price} {currency}")
                    st.write(f"🖼️ {photo_count} photos")
                
                with col2:
                    # Publish button
                    if st.button(f"🚀 Publish", key=f"pub_{listing_id}"):
                        with st.spinner("Publishing..."):
                            success, message = publish_draft(api_key, listing_id)
                            if success:
                                st.success(f"✅ Published!")
                                # Remove from session state or refresh
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                
                with col3:
                    # Delete button (optional)
                    if st.button(f"🗑️ Delete", key=f"del_{listing_id}"):
                        with st.spinner("Deleting..."):
                            success, message = delete_draft(api_key, listing_id)
                            if success:
                                st.success(f"✅ Deleted!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                
                # Show first photo if available
                if photos and len(photos) > 0:
                    try:
                        first_photo = photos[0]
                        if '_links' in first_photo and 'small' in first_photo['_links']:
                            img_url = first_photo['_links']['small']['href']
                            st.image(img_url, width=100)
                    except:
                        pass
                
                st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh Drafts"):
            with st.spinner("Refreshing..."):
                drafts, error = get_my_drafts(api_key)
                if not error:
                    st.session_state.drafts = drafts
                    st.rerun()
else:
    st.info("👆 Enter your API Key to view your drafts")

# Instructions
st.markdown("---")
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Get your API Key** from [Reverb Developers](https://reverb.com/developers)
    2. Make sure your API key has **write permissions**
    3. Enter your API Key above
    4. Click **"Load My Drafts"** to see all your drafts
    5. Use **Publish** button to publish any draft instantly
    6. Use **Delete** button to remove drafts (optional)
    
    ✅ No downloading images
    ✅ No local storage
    ✅ Direct access to your Reverb drafts
    ✅ One-click publish
    """)

st.markdown("---")
st.markdown("Made with 🎸 | Simple Reverb Draft Manager")