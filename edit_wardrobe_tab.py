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

def edit_wardrobe_tab(tracker: WardrobeTracker):
    """
    Implements the edit wardrobe interface allowing users to modify wardrobe items.
    
    Args:
        tracker: WardrobeTracker instance
            Must provide methods:
            - base64_to_image()
            - update_item()
            - move_to_listings()
            - save_database()
            Must have attribute:
            - database containing 'items' and 'outfits'
    """
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
            with st.form(key=f"form_{item['id']}_{item['collection']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if 'image' in item:
                        image = tracker.base64_to_image(item['image'])
                        if image:
                            st.image(image, width=200)
                    
                    new_wear_count = st.number_input(
                        "Times worn",
                        min_value=0,
                        value=item.get('wear_count', 0),
                        key=f"wear_count_{item['id']}_{item['collection']}"
                    )
                
                with col2:
                    new_last_worn = st.date_input(
                        "Last worn date",
                        value=datetime.fromisoformat(item["last_worn"]).date(),
                        max_value=datetime.now().date(),
                        key=f"last_worn_{item['id']}_{item['collection']}"
                    )
                    
                    days_since = (datetime.now().date() - new_last_worn).days
                    days_remaining = max(0, 7 - days_since)
                    st.warning(f"⏳ {days_remaining} days remaining")
                
                # Place 'Update' and 'Delete' buttons inside the form
                submitted = st.form_submit_button("Update")
                delete_clicked = st.form_submit_button("Delete Item")
                
                if submitted:
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
                        
                if delete_clicked:
                    collection = item['collection']
                    tracker.database[collection] = [
                        x for x in tracker.database[collection] 
                        if x['id'] != item['id']
                    ]
                    tracker.save_database()
                    st.success("🗑️ Item deleted!")