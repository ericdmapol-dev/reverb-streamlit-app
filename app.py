import streamlit as st
import requests
import os
from pathlib import Path
import time
import json

# Page configuration
st.set_page_config(page_title="Reverb Cloner PRO", page_icon="🎸", layout="centered")
st.title("🎸 Reverb Cloner PRO MAX - WITH PUBLISHING")
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
        "shipping_profile_id": int(shipping_profile_id),
        "state": "draft"  # Create as draft first
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
            st.warning(f"Could not publish listing: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.warning(f"Error publishing listing: {e}")
        return False

def wait_for_listing_ready(api_key, listing_id, max_attempts=10):
    """Wait for listing to be ready for image upload"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0"
    }
    
    st.write("⏳ Waiting for listing to be ready...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(
                f"{API_BASE}/listings/{listing_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                st.write(f"✅ Listing is ready (attempt {attempt+1})")
                return True
            else:
                st.write(f"⏳ Listing not ready yet (attempt {attempt+1}, status: {response.status_code})")
                
        except:
            st.write(f"⏳ Waiting... (attempt {attempt+1})")
        
        time.sleep(3)  # Wait 3 seconds between attempts
    
    st.warning("Listing did not become ready in time")
    return False

# ===== UPLOAD FUNCTION WITH RETRY =====
def upload_images(api_key, listing_id, image_paths):
    """Upload images to the new listing with retry logic"""
    if not image_paths:
        st.warning("No images to upload")
        return False
    
    # First, wait for listing to be ready
    if not wait_for_listing_ready(api_key, listing_id):
        st.error("Listing is not ready for image upload")
        return False
    
    # Try different endpoints
    endpoints_to_try = [
        f"https://api.reverb.com/api/listings/{listing_id}/photos",
        f"https://api.reverb.com/api/listings/{listing_id}/images",
        f"https://api.reverb.com/api/listings/{listing_id}/photos/upload",
        f"https://api.reverb.com/api/listings/{listing_id}/images/upload"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept-Version": "3.0",
    }

    progress_bar = st.progress(0)
    status_text = st.empty()
    successful_uploads = 0
    
    st.subheader("📤 Uploading Images")
    
    # Find working endpoint
    working_endpoint = None
    for endpoint in endpoints_to_try:
        try:
            st.write(f"Testing endpoint: {endpoint}")
            # Just test with headers, no file
            test_response = requests.options(endpoint, headers=headers, timeout=5)
            if test_response.status_code != 404:
                working_endpoint = endpoint
                st.write(f"✅ Found potential endpoint: {endpoint}")
                break
        except:
            continue
    
    if not working_endpoint:
        # Default to first endpoint
        working_endpoint = endpoints_to_try[0]
        st.write(f"📌 Using default endpoint: {working_endpoint}")
    
    # Upload images
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
            
            # Try multiple field names
            field_names = ["photo", "file", "image", "upload"]
            uploaded = False
            
            for field_name in field_names:
                try:
                    with open(image_path, "rb") as img_file:
                        files = {
                            field_name: (f"image_{i}.jpg", img_file, "image/jpeg")
                        }
                        
                        # Add delay between uploads
                        if i > 0:
                            time.sleep(2)
                        
                        upload_response = requests.post(
                            working_endpoint,
                            headers=headers,
                            files=files,
                            timeout=30
                        )
                    
                    if upload_response.status_code in [200, 201, 202, 204]:
                        successful_uploads += 1
                        st.write(f"✅ Uploaded image {i+1} (field: {field_name})")
                        uploaded = True
                        break
                    else:
                        st.write(f"Field '{field_name}': {upload_response.status_code}")
                        
                except Exception as e:
                    st.write(f"Field '{field_name}' error: {str(e)[:50]}")
            
            if not uploaded:
                st.warning(f"❌ Failed to upload image {i+1}")
                
        except Exception as e:
            st.warning(f"Error with image {i+1}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(image_paths))
    
    status_text.text(f"Upload complete! {successful_uploads}/{len(image_paths)} images uploaded")
    progress_bar.empty()
    
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
    
    auto_publish = st.checkbox(
        "Auto-publish listing",
        value=True,
        help="Automatically publish the listing after image upload"
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ Instructions")
    st.markdown("""
    1. Enter your Reverb API key
    2. Enter your Shipping Profile ID
    3. Paste the listing URL you want to clone
    4. Click 'Start Cloning'
    """)

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
        
        # Wait a bit for the listing to be fully created
        time.sleep(5)
        
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
st.markdown("Made with 🎸 for Reverb sellers")