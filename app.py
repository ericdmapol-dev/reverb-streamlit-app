import streamlit as st
import requests
import os
from pathlib import Path
import time
import json

# Page configuration
st.set_page_config(page_title="Reverb Cloner PRO", page_icon="🎸", layout="centered")
st.title("🎸 Reverb Cloner PRO MAX - FINAL FIX")
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

def safe_extract_make_model(listing):
    """Extract make and model safely"""
    make = listing.get("make")
    model = listing.get("model")

    if isinstance(make, dict):
        make_name = make.get("name", "Unknown")
    elif isinstance(make, str):
        make_name = make
    else:
        make_name = "Unknown"

    if isinstance(model, str):
        model_name = model
    else:
        model_name = "Unknown"

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
    """Create new listing based on original"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    make_name, model_name = safe_extract_make_model(original_listing)
    
    # Calculate new price
    original_price = float(original_listing["price"]["amount"])
    new_price = round(original_price * price_multiplier, 2)

    # Prepare payload
    payload = {
        "title": original_listing.get("title", "No Title"),
        "description": original_listing.get("description", ""),
        "price": {
            "amount": new_price,
            "currency": original_listing["price"]["currency"]
        },
        "condition": {
            "uuid": original_listing["condition"]["uuid"]
        },
        "make": make_name,
        "model": model_name,
        "shipping_profile_id": int(shipping_profile_id)
    }

    try:
        response = requests.post(
            f"{API_BASE}/listings",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code not in [200, 201]:
            st.error(f"Error creating listing: {response.status_code} - {response.text}")
            return None

        data = response.json()

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

# ===== FIXED UPLOAD FUNCTION - VERSION 3 =====
def upload_images(api_key, listing_id, image_paths):
    """Upload images to the new listing - FINAL FIX"""
    if not image_paths:
        st.warning("No images to upload")
        return False
    
    # Try different possible endpoints
    endpoints_to_try = [
        f"https://api.reverb.com/api/listings/{listing_id}/photos",
        f"https://api.reverb.com/api/listings/{listing_id}/images",
        f"https://api.reverb.com/api/listings/{listing_id}/photos/upload",
        f"https://api.reverb.com/api/listings/{listing_id}/images/upload",
        f"https://api.reverb.com/api/my/listings/{listing_id}/photos"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
    }

    progress_bar = st.progress(0)
    status_text = st.empty()
    successful_uploads = 0
    
    st.subheader("📤 Uploading Images Debug")
    
    # First, let's test which endpoint works
    working_endpoint = None
    st.write("🔍 Testing endpoints...")
    
    for endpoint in endpoints_to_try:
        try:
            # Just do a simple test with a small file if available
            if image_paths:
                with open(image_paths[0], "rb") as test_file:
                    test_files = {"photo": ("test.jpg", test_file, "image/jpeg")}
                    test_response = requests.post(
                        endpoint,
                        headers=headers,
                        files=test_files,
                        timeout=10
                    )
                    st.write(f"Endpoint: {endpoint} -> Status: {test_response.status_code}")
                    if test_response.status_code not in [404, 405]:
                        working_endpoint = endpoint
                        st.write(f"✅ Found working endpoint: {endpoint}")
                        break
        except:
            continue
    
    if not working_endpoint:
        working_endpoint = endpoints_to_try[0]  # Default to first
    
    st.write(f"📌 Using endpoint: {working_endpoint}")
    
    # Now upload all images
    for i, image_path in enumerate(image_paths):
        status_text.text(f"Uploading image {i+1} of {len(image_paths)}")
        st.write(f"--- Uploading image {i+1}: {os.path.basename(image_path)} ---")
        
        try:
            # Check if file exists and has content
            if not os.path.exists(image_path):
                st.warning(f"⚠️ Image file not found: {image_path}")
                continue
                
            file_size = os.path.getsize(image_path)
            st.write(f"File size: {file_size} bytes")
            
            if file_size == 0:
                st.warning(f"⚠️ Image file is empty: {image_path}")
                continue
            
            # Try different field names
            field_names_to_try = ["photo", "file", "image", "upload", "photos", "images"]
            
            uploaded = False
            
            for field_name in field_names_to_try:
                if uploaded:
                    break
                    
                st.write(f"Trying field name: '{field_name}'")
                
                # Open and upload image
                with open(image_path, "rb") as img_file:
                    files = {
                        field_name: (f"image_{i}.jpg", img_file, "image/jpeg")
                    }
                    
                    # Add delay between uploads
                    if i > 0:
                        time.sleep(2)
                    
                    # Make the upload request
                    upload_response = requests.post(
                        working_endpoint,
                        headers=headers,
                        files=files,
                        timeout=30
                    )
                
                st.write(f"Response status: {upload_response.status_code}")
                
                if upload_response.status_code in [200, 201, 202, 204]:
                    successful_uploads += 1
                    st.write(f"✅ SUCCESS with field name '{field_name}'")
                    uploaded = True
                    if upload_response.text:
                        try:
                            response_json = upload_response.json()
                            st.write(f"Response: {json.dumps(response_json, indent=2)[:200]}")
                        except:
                            st.write(f"Response: {upload_response.text[:200]}")
                    break
                else:
                    st.write(f"❌ Failed with field name '{field_name}': HTTP {upload_response.status_code}")
            
            if not uploaded:
                st.write(f"❌ All field names failed for image {i+1}")
            
        except requests.exceptions.Timeout:
            st.warning(f"⏱️ Timeout uploading image {i+1}")
        except requests.exceptions.RequestException as e:
            st.warning(f"🌐 Network error uploading image {i+1}: {str(e)}")
        except Exception as e:
            st.warning(f"❌ Error uploading image {i+1}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(image_paths))
    
    status_text.text(f"Upload complete! {successful_uploads}/{len(image_paths)} images uploaded successfully")
    progress_bar.empty()
    
    if successful_uploads == 0:
        st.error("❌ No images were uploaded. Please check your API permissions.")
        st.info("💡 Make sure your API key has write permissions for listings.")
    
    return successful_uploads > 0

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
    
    st.markdown("---")
    st.markdown("### ℹ️ Instructions")
    st.markdown("""
    1. Enter your Reverb API key
    2. Enter your Shipping Profile ID
    3. Paste the listing URL you want to clone
    4. Click 'Start Cloning'
    """)
    
    st.markdown("---")
    st.markdown("### 🔑 API Permissions")
    st.markdown("Make sure your API key has **write** permissions for listings!")

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
        
        st.info(f"📋 Listing ID: {listing_id}")
        
        # Fetch original listing
        original_listing = get_listing(api_key, listing_id)
        
        if not original_listing:
            st.stop()
        
        # Download images
        st.info("📥 Downloading images...")
        image_paths = download_images(original_listing)
        st.success(f"✅ Downloaded {len(image_paths)} images")
        
        # Create new listing
        st.info("📝 Creating new listing...")
        new_listing_id = create_listing(api_key, original_listing, shipping_profile_id, price_multiplier)
        
        if not new_listing_id:
            # Cleanup on failure
            cleanup_images(image_paths, keep_images=True)
            st.stop()
        
        st.success(f"✅ Created new listing with ID: {new_listing_id}")
        
        # Upload images
        if image_paths:
            st.info("📤 Uploading images...")
            upload_success = upload_images(api_key, new_listing_id, image_paths)
            
            if upload_success:
                st.success("✅ All images uploaded successfully")
            else:
                st.warning("⚠️ Some images failed to upload")
        
        # Cleanup
        cleanup_images(image_paths, keep_images)
        
        # Success message
        st.balloons()
        st.success("🎉 Clone completed successfully!")
        
        # Show link to new listing
        st.markdown(f"🔗 [View your new listing](https://reverb.com/item/{new_listing_id})")

# Add footer
st.markdown("---")
st.markdown("Made with 🎸 for Reverb sellers")