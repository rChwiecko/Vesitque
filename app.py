import streamlit as st
from PIL import Image
import numpy as np
from datetime import datetime, timedelta
from feature_extractor import FeatureExtractor
from wardrobe_tracker import WardrobeTracker
import time  
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

        # Default reset period for new items
        st.divider()
        st.subheader("Default Reset Period")
        new_reset_period = st.number_input(
            "Days until reset for new items", 
            min_value=1, 
            max_value=30, 
            value=tracker.reset_period
        )
        if new_reset_period != tracker.reset_period:
            tracker.reset_period = new_reset_period
            st.success(f"Default reset period updated to {new_reset_period} days!")

    # Main content
    tab1, tab2, tab3 = st.tabs(["Capture", "My Wardrobe", "Edit Wardrobe"])
    
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
                if 'image' in item:
                    matched_image = tracker.base64_to_image(item['image'])
                    if matched_image:
                        st.image(matched_image, caption="Matched Item", use_column_width=True)
                
                if debug_mode:
                    st.write("Match details:", item)
                    
            elif status == "too_soon":
                # Use item-specific reset period
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
                        list(tracker.clothing_categories.keys())[:-1]
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
        
    with tab3:
        st.subheader("Edit Wardrobe Items")
        
        all_items = (
            [{"collection": "items", **item} for item in tracker.database["items"]] +
            [{"collection": "outfits", **outfit} for outfit in tracker.database["outfits"]]
        )
        
        if not all_items:
            st.info("Your wardrobe is empty! Add some items first.")
            return
            
        for item in all_items:
            with st.expander(f"{item.get('name', item['type'])}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if 'image' in item:
                        image = tracker.base64_to_image(item['image'])
                        if image:
                            st.image(image, width=200)
                            
                    # Add wear count editor with current value
                    current_wear_count = item.get('wear_count', 0)
                    new_wear_count = st.number_input(
                        "Times worn",
                        min_value=0,
                        value=int(current_wear_count),  # Convert to int to ensure proper type
                        key=f"wear_count_{item['id']}_{item['collection']}"
                    )
                
                with col2:
                    current_last_worn = datetime.fromisoformat(item["last_worn"])
                    new_last_worn = st.date_input(
                        "Last worn date",
                        value=current_last_worn.date(),
                        max_value=datetime.now().date(),
                        key=f"date_{item['id']}_{item['collection']}"
                    )
                    
                    days_since = (datetime.now().date() - new_last_worn).days
                    days_remaining = max(0, 7 - days_since)
                    
                    st.warning(f"⏳ {days_remaining} days remaining")
                    
                    if st.button("Update", key=f"update_{item['id']}"):
                        # Use the new update function
                        success = tracker.update_item(
                            item['id'],
                            item['collection'],
                            datetime.combine(new_last_worn, datetime.min.time()).isoformat(),
                            new_wear_count
                        )
                        if success:
                            st.success("✅ Item updated!")
                            time.sleep(0.5)  # Small delay to ensure the success message is seen
                            st.rerun()
                    
                    if st.button("Delete Item", key=f"delete_{item['id']}", type="secondary"):
                        collection = item['collection']
                        tracker.database[collection] = [
                            x for x in tracker.database[collection] 
                            if x['id'] != item['id']
                        ]
                        tracker.save_database()
                        st.success("🗑️ Item deleted!")
                        st.rerun()

if __name__ == "__main__":
    main()