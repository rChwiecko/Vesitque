import streamlit as st
from PIL import Image
import numpy as np
from datetime import datetime
from feature_extractor import FeatureExtractor
from wardrobe_tracker import WardrobeTracker

def main():
    st.title("VESTIQUE - Smart Wardrobe Assistant")
    
    feature_extractor = FeatureExtractor()
    tracker = WardrobeTracker(feature_extractor)

    # Sidebar controls
    with st.sidebar:
        st.subheader("Settings")
        mode = st.radio(
            "Capture Mode",
            ["Single Item", "Full Outfit"],
            help="Choose whether to capture a single clothing item or a full outfit"
        )
        
        if st.button("Load Demo Data"):
            tracker.add_demo_data()
        
        debug_mode = st.checkbox("Debug Mode")
        st.session_state['debug_mode'] = debug_mode

    # Main content
    tab1, tab2 = st.tabs(["Capture", "My Wardrobe"])
    
    with tab1:
        st.subheader("Capture New Item" if mode == "Single Item" else "Capture Outfit")
        camera = st.camera_input(
            "Take a photo" if mode == "Single Item" else "Take a photo of your outfit"
        )
        
        if camera:
            image = Image.open(camera)
            
            # Process image
            status, item, similarity = tracker.process_image(
                image, 
                is_outfit=(mode == "Full Outfit")
            )
            
            if status == "existing":
                st.success(f"✅ Found matching {item['type']}! (Similarity: {similarity:.3f})")
                # Show the matching image
                if 'image' in item:
                    matched_image = tracker.base64_to_image(item['image'])
                    if matched_image:
                        st.image(matched_image, caption="Matched Item", use_column_width=True)
                
                if debug_mode:
                    st.write("Match details:", item)
                    
            elif status == "too_soon":
                days_since = (datetime.now() - datetime.fromisoformat(item["last_worn"])).days
                days_remaining = max(0, 7 - days_since)
                st.warning(f"⚠️ This {item['type']} needs {days_remaining} more days to reset!")
                
                # Show the matched item that needs to reset
                if 'image' in item:
                    matched_image = tracker.base64_to_image(item['image'])
                    if matched_image:
                        st.image(matched_image, caption="Recently Worn Item", use_column_width=True)
                
            elif status == "new":
                st.info("🆕 New item detected!")
                
                # Show the captured image
                st.image(image, caption="Captured Image", use_column_width=True)
                
                if mode == "Single Item":
                    item_type = st.selectbox(
                        "What type of clothing is this?",
                        list(tracker.clothing_categories.keys())[:-1]  # Exclude Full Outfit
                    )
                    name = st.text_input("Give this item a name (optional):", 
                                       value=f"My {item_type}")
                else:
                    item_type = "Full Outfit"
                    name = st.text_input("Give this outfit a name:", "My New Outfit")
                
                if st.button("Add to Wardrobe"):
                    success = tracker.add_new_item(
                        image, 
                        item_type,
                        is_outfit=(mode == "Full Outfit"),
                        name=name
                    )
                    if success:
                        st.success("✅ Added to wardrobe!")
    
    with tab2:
        tracker.display_wardrobe_grid()

if __name__ == "__main__":
    main()