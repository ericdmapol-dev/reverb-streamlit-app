import streamlit as st
import requests
import os
from pathlib import Path
import time
import json
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Reverb Cloner PRO", page_icon="🎸", layout="centered")
st.title("🎸 Reverb Cloner PRO - Local Drafts Manager")
st.markdown("---")

API_BASE = "https://api.reverb.com/api"
DRAFTS_FILE = "local_drafts.json"

# ===== Functions to manage local drafts =====
def load_drafts():
    """Load drafts from local JSON file"""
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_draft(draft_data):
    """Save a new draft to local file"""
    drafts = load_drafts()
    
    # Add metadata
    draft_data['_local_id'] = str(int(time.time()))
    draft_data['_created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draft_data['_published'] = False
    
    drafts.append(draft_data)
    
    with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)
    
    return draft_data['_local_id']

def update_draft(local_id, updated_data):
    """Update an existing draft"""
    drafts = load_drafts()
    for i, draft in enumerate(drafts):
        if draft.get('_local_id') == local_id:
            # Preserve metadata
            updated_data['_local_id'] = draft['_local_id']
            updated_data['_created_at'] = draft['_created_at']
            updated_data['_published'] = draft.get('_published', False)
            drafts[i] = updated_data
            break
    
    with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)

def delete_draft(local_id):
    """Delete a draft"""
    drafts = load_drafts()
    drafts = [d for d in drafts if d.get('_local_id') != local_id]
    
    with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)

def mark_as_published(local_id, reverb_listing_id):
    """Mark a draft as published with Reverb ID"""
    drafts = load_drafts()
    for i, draft in enumerate(drafts):
        if draft.get('_local_id') == local_id:
            drafts[i]['_published'] = True
            drafts[i]['_published_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            drafts[i]['_reverb_listing_id'] = reverb_listing_id
            break
    
    with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)

# ===== Original Reverb API functions =====
def extract_listing_id(url):
    """Extract listing ID from Reverb URL"""
    try:
        if "/item/" in url:
            part = url.split("/item/")[1]
            return part.split("-")[0]
        elif "reverb.com/item/" in url:
            part = url.split("reverb.com/item/")[1]
            return part.split("-")[0]
        else:
            return None
    except Exception as e:
        st.error(f"Error parsing URL: {e}")
        return None

def get_listing(api_key, listing_id):
    """Fetch original listing data"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            f"{API_BASE}/listings/{listing_id}",
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            st.error(f"Error fetching listing: {response.status_code} - {response.text}")
            return None

        return response.json()
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def extract_make_model(listing):
    """Extract make and model correctly from listing"""
    
    # Try to get make
    make = listing.get("make")
    make_name = "Unknown"
    
    if make:
        if isinstance(make, dict):
            make_name = make.get("name", "Unknown")
            if not make_name or make_name == "Unknown":
                make_name = str(make.get("_id", "Unknown"))
        elif isinstance(make, str):
            make_name = make
        elif isinstance(make, (int, float)):
            make_name = str(make)
    
    # Try to get model
    model = listing.get("model")
    model_name = "Unknown"
    
    if model:
        if isinstance(model, dict):
            model_name = model.get("name", "Unknown")
            if not model_name or model_name == "Unknown":
                model_name = str(model.get("_id", "Unknown"))
        elif isinstance(model, str):
            model_name = model
        elif isinstance(model, (int, float)):
            model_name = str(model)
    
    return make_name, model_name

def download_images(listing):
    """Download images from original listing and return local paths"""
    photos = listing.get("photos", [])
    paths = []
    
    if not photos:
        st.warning("No images found in this listing")
        return []
    
    # Create images directory
    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)
    
    # Create a subfolder with timestamp for this draft
    timestamp = int(time.time())
    draft_images_dir = images_dir / f"draft_{timestamp}"
    draft_images_dir.mkdir(exist_ok=True)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, photo in enumerate(photos):
        status_text.text(f"Downloading image {i+1} of {len(photos)}")
        
        try:
            # Try different possible image URL locations
            image_url = None
            
            if "_links" in photo:
                if "full" in photo["_links"]:
                    image_url = photo["_links"]["full"]["href"]
                elif "download" in photo["_links"]:
                    image_url = photo["_links"]["download"]["href"]
                elif "original" in photo["_links"]:
                    image_url = photo["_links"]["original"]["href"]
            elif "href" in photo:
                image_url = photo["href"]
            
            if not image_url:
                # Try to find any image URL in the photo object
                for key in photo:
                    if isinstance(photo[key], str) and photo[key].startswith(('http', 'https')):
                        image_url = photo[key]
                        break
            
            if not image_url:
                st.warning(f"Could not find image URL for image {i+1}")
                continue
            
            # Download image with timeout
            img_response = requests.get(image_url, timeout=15)
            
            if img_response.status_code == 200:
                file_path = draft_images_dir / f"img_{i}.jpg"
                
                with open(file_path, "wb") as f:
                    f.write(img_response.content)
                
                paths.append(str(file_path))
                st.write(f"✅ Downloaded image {i+1}")
            else:
                st.warning(f"Failed to download image {i+1}: HTTP {img_response.status_code}")
            
        except Exception as e:
            st.warning(f"Error downloading image {i+1}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(photos))

    status_text.text("All images downloaded!")
    progress_bar.empty()
    
    return paths

def prepare_draft_data(original_listing, shipping_profile_id, price_multiplier, image_paths):
    """Prepare listing data for local draft"""
    
    # Extract make and model correctly
    make_name, model_name = extract_make_model(original_listing)
    
    # Calculate new price
    original_price = float(original_listing["price"]["amount"])
    new_price = round(original_price * price_multiplier, 2)
    
    # Get condition
    condition = original_listing.get("condition", {})
    condition_uuid = None
    if isinstance(condition, dict):
        condition_uuid = condition.get("uuid")
    
    # Get description
    description = original_listing.get("description", "")
    
    # Get title
    title = original_listing.get("title", f"{make_name} {model_name}".strip())
    
    # Get finish if available
    finish = original_listing.get("finish", "")
    
    # Get year if available
    year = original_listing.get("year", "")
    
    # Get categories if available
    categories = original_listing.get("categories", [])
    category_uuids = []
    for cat in categories:
        if isinstance(cat, dict) and "uuid" in cat:
            category_uuids.append(cat["uuid"])
    
    # Prepare draft data
    draft_data = {
        "original_listing_id": original_listing.get("id"),
        "original_url": f"https://reverb.com/item/{original_listing.get('id')}",
        "title": title,
        "description": description,
        "price": {
            "amount": new_price,
            "currency": original_listing["price"]["currency"],
            "original_amount": original_price
        },
        "condition": {
            "uuid": condition_uuid,
            "display_name": condition.get("display_name") if isinstance(condition, dict) else "Unknown"
        },
        "make": make_name,
        "model": model_name,
        "finish": finish,
        "year": year,
        "shipping_profile_id": int(shipping_profile_id),
        "category_uuids": category_uuids,
        "image_paths": image_paths,
        "image_count": len(image_paths)
    }
    
    return draft_data

def publish_to_reverb(api_key, draft_data):
    """Publish a local draft to Reverb"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Prepare payload for Reverb
    payload = {
        "title": draft_data["title"],
        "description": draft_data["description"],
        "price": {
            "amount": draft_data["price"]["amount"],
            "currency": draft_data["price"]["currency"]
        },
        "condition": {
            "uuid": draft_data["condition"]["uuid"]
        },
        "make": draft_data["make"],
        "model": draft_data["model"],
        "finish": draft_data.get("finish", ""),
        "year": draft_data.get("year", ""),
        "shipping_profile_id": draft_data["shipping_profile_id"],
        "state": "draft"
    }
    
    if draft_data.get("category_uuids"):
        payload["category_uuids"] = draft_data["category_uuids"]
    
    st.write("📤 Creating listing on Reverb...")
    
    try:
        response = requests.post(
            f"{API_BASE}/listings",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code not in [200, 201]:
            return None, f"Error creating listing: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Extract listing ID
        listing_id = None
        if isinstance(data, dict):
            if "listing" in data and isinstance(data["listing"], dict):
                listing_id = data["listing"].get("id")
            elif "id" in data:
                listing_id = data["id"]
        
        if not listing_id:
            return None, "Could not extract listing ID from response"
        
        # Upload images if available
        if draft_data.get("image_paths"):
            st.write("📤 Uploading images...")
            upload_success = upload_images_to_reverb(api_key, listing_id, draft_data["image_paths"])
            if not upload_success:
                return listing_id, "⚠️ Listing created but image upload failed"
        
        return listing_id, "✅ Listing created successfully!"
        
    except Exception as e:
        return None, f"Connection error: {e}"

def upload_images_to_reverb(api_key, listing_id, image_paths):
    """Upload images to a Reverb listing"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
    }
    
    upload_url = f"{API_BASE}/listings/{listing_id}/photos"
    successful_uploads = 0
    
    for i, image_path in enumerate(image_paths):
        try:
            if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
                continue
            
            with open(image_path, "rb") as img_file:
                files = {'photo': (f'image_{i}.jpg', img_file, 'image/jpeg')}
                response = requests.post(upload_url, headers=headers, files=files, timeout=30)
                
                if response.status_code in [200, 201, 202, 204]:
                    successful_uploads += 1
            
            time.sleep(1)  # Small delay between uploads
            
        except Exception:
            continue
    
    return successful_uploads > 0

# ===== Streamlit UI =====
tab1, tab2 = st.tabs(["📥 Extract Listing", "📋 My Local Drafts"])

with tab1:
    st.header("Extract Listing to Local Draft")
    
    with st.sidebar:
        st.header("⚙️ Settings")
        price_multiplier = st.slider(
            "Price Multiplier", 
            min_value=0.1, 
            max_value=2.0, 
            value=0.7,
            step=0.05,
            help="Multiply original price by this value"
        )
    
    # Inputs
    api_key = st.text_input("🔑 API Key", type="password", help="Enter your Reverb API key")
    shipping_profile_id = st.text_input("📦 Shipping Profile ID", help="Enter your Shipping Profile ID")
    listing_url = st.text_input("🔗 Listing URL", help="Paste the Reverb listing URL to extract")
    
    if st.button("📥 Extract to Local Draft", type="primary", use_container_width=True):
        if not api_key or not shipping_profile_id or not listing_url:
            st.error("❌ Please fill all fields")
        else:
            with st.spinner("Extracting listing..."):
                # Extract listing ID
                listing_id = extract_listing_id(listing_url)
                if not listing_id:
                    st.error("❌ Invalid URL")
                    st.stop()
                
                # Fetch listing
                original_listing = get_listing(api_key, listing_id)
                if not original_listing:
                    st.stop()
                
                # Download images
                st.info("📥 Downloading images...")
                image_paths = download_images(original_listing)
                
                # Prepare draft data
                draft_data = prepare_draft_data(
                    original_listing, 
                    shipping_profile_id, 
                    price_multiplier,
                    image_paths
                )
                
                # Save to local drafts
                local_id = save_draft(draft_data)
                
                st.success(f"✅ Listing saved as local draft!")
                st.info(f"📌 Draft ID: {local_id}")
                st.info(f"🖼️ Images: {len(image_paths)} downloaded")

with tab2:
    st.header("My Local Drafts")
    
    drafts = load_drafts()
    
    if not drafts:
        st.info("No local drafts yet. Extract a listing first!")
    else:
        # Filter options
        show_published = st.checkbox("Show published drafts", value=False)
        
        filtered_drafts = drafts
        if not show_published:
            filtered_drafts = [d for d in drafts if not d.get('_published', False)]
        
        for draft in filtered_drafts:
            with st.expander(f"📝 {draft.get('title', 'Untitled')}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Make:** {draft.get('make', 'Unknown')}")
                    st.write(f"**Model:** {draft.get('model', 'Unknown')}")
                    st.write(f"**Price:** ${draft.get('price', {}).get('amount', 0)}")
                    st.write(f"**Images:** {draft.get('image_count', 0)}")
                    st.write(f"**Created:** {draft.get('_created_at', 'Unknown')}")
                    
                    if draft.get('_published'):
                        st.success(f"✅ Published - Reverb ID: {draft.get('_reverb_listing_id')}")
                
                with col2:
                    if not draft.get('_published'):
                        if st.button(f"🚀 Publish Now", key=f"pub_{draft['_local_id']}"):
                            # Show publish dialog
                            with st.spinner("Publishing to Reverb..."):
                                pub_api_key = st.text_input("Enter API Key to publish", type="password", key=f"api_{draft['_local_id']}")
                                if pub_api_key:
                                    listing_id, message = publish_to_reverb(pub_api_key, draft)
                                    if listing_id:
                                        mark_as_published(draft['_local_id'], listing_id)
                                        st.success(f"✅ Published! ID: {listing_id}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{draft['_local_id']}"):
                        # Optional: delete image files
                        if draft.get('image_paths'):
                            for img_path in draft['image_paths']:
                                try:
                                    if os.path.exists(img_path):
                                        os.remove(img_path)
                                except:
                                    pass
                        
                        delete_draft(draft['_local_id'])
                        st.success("Draft deleted!")
                        st.rerun()
                
                # Show image previews
                if draft.get('image_paths'):
                    st.write("**Image Previews:**")
                    preview_cols = st.columns(4)
                    for idx, img_path in enumerate(draft['image_paths'][:4]):  # Show first 4
                        if os.path.exists(img_path):
                            with preview_cols[idx]:
                                st.image(img_path, width=100)

# Add footer
st.markdown("---")
st.markdown("Made with 🎸 | Local Drafts Manager v1.0")