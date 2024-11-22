"""
capture_tab.py

This module handles the capture functionality for the Vestique wardrobe assistant.
Allows users to capture and process new clothing items and outfits.
"""

import streamlit as st
from PIL import Image
from datetime import datetime
from wardrobe_tracker import WardrobeTracker

def capture_tab(mode: str, tracker: WardrobeTracker, debug_mode: bool):
    """
    Implements the capture tab functionality for the Vestique wardrobe assistant.
    
    Args:
        mode (str): Either 'Single Item' or 'Full Outfit'
        tracker (WardrobeTracker): The wardrobe tracker instance
        debug_mode (bool): Whether debug mode is enabled
    """
    st.subheader("Capture New Item" if mode == "Single Item" else "Capture Outfit")
    # Fix for first run
    # Initialize session state variables
    if 'current_image' not in st.session_state:
        st.session_state['current_image'] = None
    if 'image_status' not in st.session_state:
        st.session_state['image_status'] = None
    if 'image_item' not in st.session_state:
        st.session_state['image_item'] = None
    if 'image_similarity' not in st.session_state:
        st.session_state['image_similarity'] = None
    # Custom CSS to force the camera layout
    st.markdown("""
        <style>
        /* Main camera container */
        .stCamera {
            background-color: #1E1E1E !important;
            border-radius: 10px !important;
            padding: 0 !important;
            margin: 0 !important;
            width: 640px !important;
            height: 480px !important;
        }
        
        /* Video feed */
        .stCamera > video {
            width: 100% !important;
            height: 100% !important;
            object-fit: cover !important;
        }
        
        /* Captured image */
        .stCamera > img {
            width: 100% !important;
            height: 100% !important;
            object-fit: contain !important;
            background-color: #1E1E1E !important;
        }
        
        /* Clear photo button section */
        .stCamera > div {
            position: absolute !important;
            bottom: 0 !important;
            width: 100% !important;
            background-color: rgba(0,0,0,0.7) !important;
            padding: 8px !important;
            border-radius: 0 0 10px 10px !important;
        }

        /* Center the camera in the page */
        [data-testid="stHorizontalBlock"] {
            justify-content: center !important;
            background-color: transparent !important;
        }

        /* Remove any extra padding/margin */
        .stApp {
            margin: 0 auto !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Camera input in center of page
    camera = st.camera_input(
        "Take a photo" if mode == "Single Item" else "Take a photo of your outfit",
        key="camera_input",
        label_visibility="hidden"
    )
    if camera is not None:
        if st.session_state['current_image'] is None:
            image = Image.open(camera)
            st.session_state['current_image'] = image

            # Process image
            status, item, similarity = tracker.process_image(
                image, 
                is_outfit=(mode == "Full Outfit")
            )

            st.session_state['image_status'] = status
            st.session_state['image_item'] = item
            st.session_state['image_similarity'] = similarity
        else:
            image = st.session_state['current_image']
            status = st.session_state['image_status']
            item = st.session_state['image_item']
            similarity = st.session_state['image_similarity']

        # Now, display based on status
        if status == "existing":
            st.success(f"✅ Found matching {item['type']}! (Similarity: {similarity:.3f})")
            if 'image' in item:
                matched_image = tracker.base64_to_image(item['image'])
                if matched_image:
                    st.image(matched_image, caption="Matched Item", use_column_width=True)
            
            if debug_mode:
                st.write("Match details:", item)
                
        elif status == "too_soon":
            reset_period = item.get('reset_period', tracker.reset_period)
            days_since = (datetime.now() - datetime.fromisoformat(item["last_worn"])).days
            days_remaining = max(0, reset_period - days_since)
            st.warning(f"⚠️ This {item['type']} needs {days_remaining} more days to reset!")
            
            if 'image' in item:
                matched_image = tracker.base64_to_image(item['image'])
                if matched_image:
                    st.image(matched_image, caption="Recently Worn Item", use_column_width=True)
            
        elif status == "new":
            st.info("🆕 New item detected!")
            st.image(image, caption="Captured Image", use_column_width=True)
            
            if mode == "Single Item":
                item_type = st.selectbox(
                    "What type of clothing is this?",
                    list(tracker.clothing_categories.keys())[:-1],
                    key='item_type_selectbox'
                )
                name = st.text_input("Give this item a name (optional):", 
                                    value=f"My {item_type}", key='item_name_input')
            else:
                item_type = "Full Outfit"
                name = st.text_input("Give this outfit a name:", "My New Outfit", key='outfit_name_input')
            
            if st.button("Add to Wardrobe"):
                try:
                    with st.spinner("Adding item to wardrobe..."):
                        success = tracker.add_new_item(
                            image,
                            item_type,
                            is_outfit=(mode == "Full Outfit"),
                            name=name
                        )
                        
                    if success:
                        st.success("✅ Added to wardrobe!")
                        # Reset the session state
                        st.session_state['current_image'] = None
                        st.session_state['image_status'] = None
                        st.session_state['image_item'] = None
                        st.session_state['image_similarity'] = None
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    # Still try to add the item without AI analysis
                    fallback_success = tracker.add_new_item_sync(
                        image,
                        item_type,
                        is_outfit=(mode == "Full Outfit"),
                        name=name
                    )
                    if fallback_success:
                        st.warning("⚠️ Added to wardrobe without AI analysis")
                    # Reset the session state
                    st.session_state['current_image'] = None
                    st.session_state['image_status'] = None
                    st.session_state['image_item'] = None
                    st.session_state['image_similarity'] = None

    else:
        # Reset session state when no camera input
        st.session_state['current_image'] = None
        st.session_state['image_status'] = None
        st.session_state['image_item'] = None
        st.session_state['image_similarity'] = None