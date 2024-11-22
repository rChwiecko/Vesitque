"""
edit_wardrobe_tab.py

This module handles the edit wardrobe functionality for the Vestique wardrobe assistant.
Allows users to modify item details, update wear counts, and manage wardrobe items.

Dependencies:
- streamlit
- datetime 
- time
- WardrobeTracker (for database and image operations)
"""

import streamlit as st
from datetime import datetime
import time
from wardrobe_tracker import WardrobeTracker

def handle_update(tracker, item, new_wear_count, new_last_worn):
    """Helper function to handle item updates."""
    days_since = (datetime.now().date() - new_last_worn).days
    
    success = tracker.update_item(
        item['id'],
        item['collection'],
        datetime.combine(new_last_worn, datetime.min.time()).isoformat(),
        int(new_wear_count)
    )
    
    if success:
        st.success("✅ Item updated!")
        
        # Check if item should be moved to marketplace
        if days_since >= 8:
            tracker.move_to_listings(item['id'], item['collection'])
            st.info("📦 Item moved to marketplace due to inactivity")
            time.sleep(0.5)
            st.rerun()
        return True
    return False

def edit_wardrobe_tab(tracker: WardrobeTracker):
    st.subheader("Edit Wardrobe Items")
    
    all_items = (
        [{"collection": "items", **item} for item in tracker.database["items"]] +
        [{"collection": "outfits", **outfit} for outfit in tracker.database["outfits"]]
    )
    
    if not all_items:
        st.info("Your wardrobe is empty! Add some items first.")
        return
        
    for item in all_items:
        item_key = f"{item['id']}_{item['collection']}"
        number_input_key = f"wear_count_{item_key}"
        date_input_key = f"last_worn_{item_key}"
        
        with st.expander(f"{item.get('name', item['type'])}"):
            with st.form(key=f"form_{item_key}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if 'image' in item:
                        image = tracker.base64_to_image(item['image'])
                        if image:
                            st.image(image, width=200)
                    
                    # Initialize widget state if not already set
                    if number_input_key not in st.session_state:
                        st.session_state[number_input_key] = int(item.get('wear_count', 0))
                    
                    new_wear_count = st.number_input(
                        "Times worn",
                        min_value=0,
                        key=number_input_key
                    )
                
                with col2:
                    last_worn = datetime.fromisoformat(item["last_worn"]).date()
                    
                    # Initialize widget state if not already set
                    if date_input_key not in st.session_state:
                        st.session_state[date_input_key] = last_worn
                    
                    new_last_worn = st.date_input(
                        "Last worn date",
                        max_value=datetime.now().date(),
                        key=date_input_key
                    )
                    
                    days_since = (datetime.now().date() - new_last_worn).days
                    days_remaining = max(0, 7 - days_since)
                    st.warning(f"⏳ {days_remaining} days remaining")
                
                col_update, col_delete = st.columns(2)
                with col_update:
                    submitted = st.form_submit_button("Update", use_container_width=True)
                with col_delete:
                    delete_clicked = st.form_submit_button("Delete Item", use_container_width=True)
                
                if submitted:
                    handle_update(tracker, item, new_wear_count, new_last_worn)
                
                if delete_clicked:
                    collection = item['collection']
                    tracker.database[collection] = [
                        x for x in tracker.database[collection] 
                        if x['id'] != item['id']
                    ]
                    tracker.save_database()
                    st.success("🗑️ Item deleted!")
                    time.sleep(0.5)
                    st.experimental_rerun()
