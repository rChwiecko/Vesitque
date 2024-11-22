# marketplace_tab.py

# Necessary imports
import streamlit as st
from datetime import datetime
import time
import json

# Import your local modules as needed
from market_place_manager import Marketplace
from decider import decide_preference
from decide_match import decide_match

def marketplace_tab(tracker, email_notifier):
    st.subheader("🛍️ Marketplace Listings")



    # Create tabs for "Your Listings" and "Others' Listings"
    tab1, tab2 = st.tabs(["Your Listings", "Others' Listings"])

    with tab1:
        # Get items that haven't been worn for 8+ days
        current_date = datetime.now().date()
        listed_items = []

        # First get existing listings
        listed_items.extend(tracker.get_listings())

        # Then check for new items that should be listed
        for item in tracker.database["items"]:
            if "last_worn" not in item:
                continue  # Skip items without last_worn date

            last_worn_date = datetime.fromisoformat(item["last_worn"]).date()
            days_since = (current_date - last_worn_date).days

            # If item should be listed and isn't already
            if days_since >= 8 and not any(listing["id"] == item["id"] for listing in listed_items):
                if tracker.move_to_listings(item["id"], "items"):
                    listed_items = tracker.get_listings()  # Refresh listings

        if listed_items:
            st.write(f"📦 {len(listed_items)} Items Available")

            for item in listed_items:
                listing_key = f"listing_content_{item['id']}"

                with st.expander(f"🏷️ {item.get('name', item['type'])}"):
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        if 'image' in item:
                            image = tracker.base64_to_image(item['image'])
                            if image:
                                st.image(image, use_column_width=True)

                        st.markdown("**Item Details:**")
                        st.markdown(f"- Type: {item['type']}")
                        st.markdown(f"- Brand: {item.get('brand', 'Not specified')}")
                        st.markdown(f"- Condition: {item.get('condition', 'Not specified')}")

                        # Handle case where neither date_listed nor last_worn exists
                        try:
                            if 'date_listed' in item:
                                listed_date = datetime.fromisoformat(item['date_listed'])
                            elif 'last_worn' in item:
                                listed_date = datetime.fromisoformat(item['last_worn'])
                            else:
                                listed_date = datetime.now()

                            days_listed = (current_date - listed_date.date()).days
                            st.markdown(f"- Listed: {days_listed} days ago")
                        except Exception as e:
                            st.markdown("- Recently listed")

                    with col2:
                        if listing_key not in st.session_state:
                            with st.spinner("Creating listing description..."):
                                listing_content = email_notifier.generate_listing_content(item)
                                if listing_content:
                                    st.session_state[listing_key] = listing_content
                                else:
                                    st.session_state[listing_key] = "Error generating listing content."

                        st.markdown(st.session_state[listing_key])

                        col3, col4 = st.columns([1, 1])
                        with col3:
                            if st.button("Refresh Listing", key=f"refresh_{item['id']}"):
                                with st.spinner("Regenerating listing..."):
                                    new_content = email_notifier.generate_listing_content(item)
                                    if new_content:
                                        st.session_state[listing_key] = new_content
                                        st.success("Listing refreshed!")

                        with col4:
                            if st.button("Remove Listing", key=f"remove_{item['id']}"):
                                if tracker.remove_from_listings(item['id']):
                                    if listing_key in st.session_state:
                                        del st.session_state[listing_key]
                                    st.success("Item removed from marketplace!")
                                    time.sleep(0.5)
                                    st.rerun()
        else:
            st.info("👋 No items currently listed! Items unworn for 8+ days will appear here automatically.")

    # with tab2:
        #     st.write("🔍 This section will show marketplace listings from other users.")
        #     # Dropdown menu for filtering
        #     filter_option = st.selectbox("Filter listings:", ["Off", "By Preference"])

        #     if filter_option == "Off":
        #         st.write("🔍 All listings are displayed here.")
        #     elif filter_option == "By Preference":
        #         st.write("🔍 Listings filtered by your preferences will appear here.")

    #     st.info("Feature coming soon!")
    with tab2:
        by_preference = False
        st.write("🔍 This section will show marketplace listings from other users.")
        # Dropdown menu for filtering
        filter_option = st.selectbox("Filter listings:", ["Off", "By Preference"])
        if filter_option == "Off":
            st.write("🔍 All listings are displayed here.")
            by_preference = False
        elif filter_option == "By Preference":
            st.write("🔍 Listings filtered by your preferences will appear here.")
            by_preference = True
        marketplace = Marketplace()


        # Get all items from the marketplace database
        listed_items = marketplace.get_all_items()

        if by_preference:
            with open('clothing_database.json', 'r') as file:
                data = json.load(file)
                contents = data.get('items', [])

            if not contents and by_preference:
                st.info("Your wardrobe is empty! Add some items to get personalized insights.")
                return

            # Find items with min and max wear count
            min_view = float('inf')
            max_view = -1
            smallest_des = None
            largest_des = None

            for item in contents:
                wear_count = item.get('wear_count', 0)
                if 'ai_analysis' in item:
                    if wear_count < min_view:
                        smallest_des = item['ai_analysis']
                        min_view = wear_count
                    if wear_count > max_view:
                        largest_des = item['ai_analysis']
                        max_view = wear_count

            if not smallest_des or not largest_des:
                st.warning("Not enough analyzed items to generate insights.")
                return


            with st.spinner("Analyzing wardrobe preferences..."):
                result = decide_preference(largest_des, smallest_des)
                results_list = json.loads(result)
                print("Res_list: ",results_list)

            # Extract liked and disliked traits from the user's wardrobe analysis
            liked_characteristics = results_list[0]
            disliked_characteristics = results_list[1]

            # Create a filtered list of items based on the user's preferences
            filtered_items = []
            for item in listed_items:
                try:
                    # Get `ai_analysis` as a raw string
                    ai_analysis_raw = item.get("ai_analysis", "").strip()

                    # Skip if `ai_analysis` is empty
                    if not ai_analysis_raw:
                        st.warning(f"Item {item.get('name', 'Unnamed')} has no valid AI analysis.")
                        continue

                    # Pass `ai_analysis` directly as the item_characteristics to the model
                    if decide_match(liked_characteristics, disliked_characteristics, ai_analysis_raw):
                        filtered_items.append(item)
                except ValueError as e:
                    st.error(f"Error analyzing item {item.get('name', 'Unnamed')}: {e}")

            # Display filtered items
            if filtered_items:
                st.write(f"🎯 {len(filtered_items)} Items Match Your Preferences")

                for item in filtered_items:
                    listing_key = f"listing_content_{item['id']}"

                    with st.expander(f"🏷️ {item.get('name', item['type'])}"):
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            if 'image' in item:
                                # Display the item's image
                                image = marketplace.base64_to_image(item['image'])
                                if image:
                                    st.image(image, use_column_width=True)

                            st.markdown("**Item Details:**")
                            st.markdown(f"- Type: {item.get('type', 'Unknown')}")
                            st.markdown(f"- Brand: {item.get('brand', 'Not specified')}")

                        with col2:
                            listing_content = f"This item matches your preferences with characteristics: {ai_analysis_raw}"
                            st.markdown(listing_content)

                            if st.button("Buy", key=f"buy_{item['id']}"):
                                # Remove the item from the marketplace
                                if marketplace.remove_item(item['id']):
                                    st.success(f"Item '{item.get('name', 'Unnamed')}' purchased successfully!")
                                    time.sleep(0.5)
                                    st.rerun()  # Refresh the UI to reflect the change
            else:
                st.info("No items match your preferences.")




        else:
            if listed_items:
                st.write(f"📦 {len(listed_items)} Items Available")

                for item in listed_items:
                    listing_key = f"listing_content_{item['id']}"

                    with st.expander(f"🏷️ {item.get('name', item['type'])}"):
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            if 'image' in item:
                                # Display the item's image
                                image = marketplace.base64_to_image(item['image'])  # Assuming base64_to_image is available
                                if image:
                                    st.image(image, use_column_width=True)

                            st.markdown("**Item Details:**")
                            st.markdown(f"- Type: {item['type']}")
                            st.markdown(f"- Brand: {item.get('brand', 'Not specified')}")
                            st.markdown(f"- Condition: {item.get('condition', 'Not specified')}")

                            # Handle case where neither date_listed nor last_worn exists
                            try:
                                if 'date_listed' in item:
                                    listed_date = datetime.fromisoformat(item['date_listed'])
                                elif 'last_worn' in item:
                                    listed_date = datetime.fromisoformat(item['last_worn'])
                                else:
                                    listed_date = datetime.now()

                                days_listed = (datetime.now().date() - listed_date.date()).days
                                st.markdown(f"- Listed: {days_listed} days ago")
                            except Exception as e:
                                st.markdown("- Recently listed")

                        with col2:
                            if listing_key not in st.session_state:
                                with st.spinner("Creating listing description..."):
                                    listing_content = email_notifier.generate_listing_content(item)
                                    if listing_content:
                                        st.session_state[listing_key] = listing_content
                                    else:
                                        st.session_state[listing_key] = "Error generating listing content."

                            st.markdown(st.session_state[listing_key])

                            col3, col4 = st.columns([1, 1])
                            with col3:
                                if st.button("Claim", key=f"claim_{item['id']}"):
                                    # Remove the item from the marketplace
                                    if marketplace.remove_item(item['id']):
                                        st.success(f"Item '{item.get('name', 'Unnamed')}' claimed successfully!")

                                        # Add the item to the wardrobe
                                        claimed_image = marketplace.base64_to_image(item["image"])
                                        success = tracker.add_new_item_sync(
                                            claimed_image,
                                            item["type"],
                                            is_outfit=False,  # Assuming it's not a full outfit
                                            name=item.get("name", item["type"])
                                        )

                                        if success:
                                            st.success("Item added to your wardrobe!")
                                        else:
                                            st.error("Failed to add the item to your wardrobe.")
            else:
                st.info("👋 No items currently listed! Items will appear here automatically.")