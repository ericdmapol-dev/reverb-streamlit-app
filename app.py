import streamlit as st
import requests
import os
from pathlib import Path
import time
import json

# Page configuration
st.set_page_config(page_title="Reverb Cloner PRO", page_icon="🎸", layout="centered")
st.title("🎸 Reverb Cloner PRO MAX - FIXED DATA")
st.markdown("---")

API_BASE = "https://api.reverb.com/api"

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
                # Try to get from string representation
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
                # Try to get from string representation
                model_name = str(model.get("_id", "Unknown"))
        elif isinstance(model, str):
            model_name = model
        elif isinstance(model, (int, float)):
            model_name = str(model)
    
    # If still unknown, try to extract from title
    if make_name == "Unknown" or model_name == "Unknown":
        title = listing.get("title", "")
        if title:
            # Try to parse make and model from title
            parts = title.split()
            if len(parts) >= 2 and not make_name or make_name == "Unknown":
                make_name = parts[0]
            if len(parts) >= 2 and not model_name or model_name == "Unknown":
                model_name = " ".join(parts[1:3]) if len(parts) > 2 else parts[1] if len(parts) > 1 else "Unknown"
    
    return make_name, model_name

def download_images(listing):
    """Download images from original listing"""
    photos = listing.get("photos", [])
    paths = []
    
    if not photos:
        st.warning("No images found in this listing")
        return []
    
    # Create images directory
    Path("images").mkdir(exist_ok=True)
    
    # Clean old images
    for old_file in Path("images").glob("*"):
        try:
            old_file.unlink()
        except:
            pass

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
                file_path = f"images/img_{i}_{int(time.time())}.jpg"
                
                with open(file_path, "wb") as f:
                    f.write(img_response.content)
                
                paths.append(file_path)
                st.write(f"✅ Downloaded image {i+1}")
            else:
                st.warning(f"Failed to download image {i+1}: HTTP {img_response.status_code}")
            
        except Exception as e:
            st.warning(f"Error downloading image {i+1}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(photos))

    status_text.text("All images downloaded!")
    progress_bar.empty()
    
    return paths

def create_listing(api_key, original_listing, shipping_profile_id, price_multiplier):
    """Create new listing based on original with correct data"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Extract make and model correctly
    make_name, model_name = extract_make_model(original_listing)
    
    st.write(f"Extracted Make: {make_name}")
    st.write(f"Extracted Model: {model_name}")
    
    # Calculate new price
    original_price = float(original_listing["price"]["amount"])
    new_price = round(original_price * price_multiplier, 2)

    # Get condition UUID
    condition_uuid = None
    condition = original_listing.get("condition")
    if condition:
        if isinstance(condition, dict):
            condition_uuid = condition.get("uuid")
        elif isinstance(condition, str):
            # If it's a string, we need to fetch the UUID
            condition_uuid = condition
    
    if not condition_uuid:
        # Default condition (Good)
        condition_uuid = "f5d1f1b0-3b3a-0133-9c5d-22000b7b5b1b"
    
    # Get description
    description = original_listing.get("description", "")
    if not description:
        description = f"Original listing: {original_listing.get('title', 'No title')}"
    
    # Get title
    title = original_listing.get("title", f"{make_name} {model_name}".strip())
    if not title or title == "Unknown":
        title = f"{make_name} {model_name}".strip()
    
    # Prepare payload - using correct Reverb API format
    payload = {
        "listing": {
            "title": title,
            "description": description,
            "price": {
                "amount": new_price,
                "currency": original_listing["price"]["currency"]
            },
            "condition": {
                "uuid": condition_uuid
            },
            "make": make_name,
            "model": model_name,
            "shipping_profile_id": int(shipping_profile_id),
            "state": "draft"
        }
    }
    
    st.write("Sending payload:")
    st.json(payload)

    try:
        response = requests.post(
            f"{API_BASE}/listings",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code not in [200, 201]:
            st.error(f"Error creating listing: {response.status_code}")
            st.error(f"Response: {response.text}")
            return None

        data = response.json()
        st.write("Response from API:")
        st.json(data)

        # Handle different response formats
        if "listing" in data:
            return data["listing"]["id"]
        elif "id" in data:
            return data["id"]
        else:
            st.error(f"Unexpected response format: {data}")
            return None
            
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def verify_listing_exists(api_key, listing_id):
    """Verify that the listing exists and is accessible"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }
    
    try:
        response = requests.get(
            f"{API_BASE}/listings/{listing_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return True
        else:
            st.write(f"Listing check: HTTP {response.status_code}")
            return False
    except Exception as e:
        st.write(f"Error checking listing: {e}")
        return False

def upload_images(api_key, listing_id, image_paths):
    """Upload images to the listing"""
    if not image_paths:
        st.warning("No images to upload")
        return False
    
    # First, verify the listing exists
    st.write("🔍 Verifying listing exists...")
    if not verify_listing_exists(api_key, listing_id):
        st.error("❌ Listing does not exist or is not accessible")
        return False
    
    # Correct endpoint according to Reverb API documentation
    upload_url = f"https://api.reverb.com/api/my/listings/{listing_id}/photos"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
    }

    progress_bar = st.progress(0)
    status_text = st.empty()
    successful_uploads = 0
    
    st.subheader("📤 Uploading Images")
    st.write(f"Using endpoint: {upload_url}")
    
    for i, image_path in enumerate(image_paths):
        status_text.text(f"Uploading image {i+1} of {len(image_paths)}")
        
        try:
            if not os.path.exists(image_path):
                st.warning(f"⚠️ Image file not found: {image_path}")
                continue
            
            file_size = os.path.getsize(image_path)
            if file_size == 0:
                st.warning(f"⚠️ Image file is empty: {image_path}")
                continue
            
            # Add delay between uploads
            if i > 0:
                time.sleep(3)
            
            # Prepare the file for upload
            with open(image_path, "rb") as img_file:
                files = {
                    'file': (f'image_{i}.jpg', img_file, 'image/jpeg')
                }
                
                # Make the upload request
                upload_response = requests.post(
                    upload_url,
                    headers=headers,
                    files=files,
                    timeout=30
                )
            
            # Check response
            st.write(f"Image {i+1} - Status: {upload_response.status_code}")
            
            if upload_response.status_code in [200, 201, 202, 204]:
                successful_uploads += 1
                st.write(f"✅ Successfully uploaded image {i+1}")
            else:
                st.write(f"❌ Failed to upload image {i+1}")
                if upload_response.text:
                    st.write(f"Error: {upload_response.text[:200]}")
            
        except Exception as e:
            st.warning(f"❌ Error: {str(e)}")
        
        progress_bar.progress((i + 1) / len(image_paths))
    
    status_text.text(f"Upload complete! {successful_uploads}/{len(image_paths)} images uploaded")
    progress_bar.empty()
    
    return successful_uploads > 0

def publish_listing(api_key, listing_id):
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
            st.write(f"✅ Listing {listing_id} published successfully")
            return True
        else:
            st.warning(f"Could not publish listing: {response.status_code}")
            if response.text:
                st.write(response.text[:200])
            return False
    except Exception as e:
        st.warning(f"Error publishing listing: {e}")
        return False

def cleanup_images(image_paths, keep_images=False):
    """Clean up downloaded images"""
    if keep_images:
        return
    
    for image_path in image_paths:
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except:
            pass

# ===== Streamlit UI =====
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
    
    keep_images = st.checkbox(
        "Keep images after upload",
        value=False,
        help="Keep downloaded images locally after upload"
    )
    
    auto_publish = st.checkbox(
        "Auto-publish listing",
        value=True,
        help="Automatically publish the listing after image upload"
    )

# Main inputs
api_key = st.text_input("🔑 API Key", type="password", help="Enter your Reverb API key")

shipping_profile_id = st.text_input("📦 Shipping Profile ID", help="Enter your Shipping Profile ID")

listing_url = st.text_input("🔗 Listing URL", help="Paste the Reverb listing URL you want to clone")

# Clone button
if st.button("🚀 Start Cloning", type="primary", use_container_width=True):
    
    # Validate inputs
    if not api_key:
        st.error("❌ Please enter your API Key")
        st.stop()
    
    if not shipping_profile_id:
        st.error("❌ Please enter your Shipping Profile ID")
        st.stop()
    
    if not listing_url:
        st.error("❌ Please enter a Listing URL")
        st.stop()
    
    # Start cloning process
    with st.spinner("Processing your request..."):
        
        # Extract listing ID
        listing_id = extract_listing_id(listing_url)
        
        if not listing_id:
            st.error("❌ Invalid URL format")
            st.stop()
        
        st.info(f"📋 Original Listing ID: {listing_id}")
        
        # Fetch original listing
        original_listing = get_listing(api_key, listing_id)
        
        if not original_listing:
            st.stop()
        
        # Download images
        st.info("📥 Downloading images...")
        image_paths = download_images(original_listing)
        st.success(f"✅ Downloaded {len(image_paths)} images")
        
        # Create new listing (as draft)
        st.info("📝 Creating new listing (draft)...")
        new_listing_id = create_listing(api_key, original_listing, shipping_profile_id, price_multiplier)
        
        if not new_listing_id:
            # Cleanup on failure
            cleanup_images(image_paths, keep_images=True)
            st.stop()
        
        st.success(f"✅ Created new draft listing with ID: {new_listing_id}")
        
        # Wait longer for the listing to be fully created
        st.write("⏳ Waiting 10 seconds for listing to be ready...")
        time.sleep(10)
        
        # Upload images
        if image_paths:
            st.info("📤 Uploading images...")
            upload_success = upload_images(api_key, new_listing_id, image_paths)
            
            if upload_success:
                st.success("✅ Images uploaded successfully")
            else:
                st.warning("⚠️ Some images failed to upload")
        
        # Publish the listing if auto-publish is enabled
        if auto_publish and new_listing_id:
            st.info("📢 Publishing listing...")
            publish_listing(api_key, new_listing_id)
        
        # Cleanup
        cleanup_images(image_paths, keep_images)
        
        # Success message
        st.balloons()
        st.success("🎉 Clone completed successfully!")
        
        # Show link to new listing
        st.markdown(f"🔗 [View your new listing](https://reverb.com/item/{new_listing_id})")

# Add footer
st.markdown("---")
st.markdown("Made with 🎸 for Reverb sellers | Fixed data extraction")