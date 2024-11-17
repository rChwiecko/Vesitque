import streamlit as st
from PIL import Image
import numpy as np
from datetime import datetime, timedelta
from feature_extractor import FeatureExtractor
from wardrobe_tracker import WardrobeTracker
from wardrobe_notifier import EmailNotifier
import time  
import asyncio  # Add this
import os
def initialize_email_settings():
    if 'email_configured' not in st.session_state:
        st.session_state.email_configured = False
        
    if 'sender_email' not in st.session_state:
        st.session_state.sender_email = ""
        
    if 'email_password' not in st.session_state:
        st.session_state.email_password = ""
def initialize_notification_state():
    if 'notification_state' not in st.session_state:
        st.session_state.notification_state = {
            'unworn_items': None,
            'show_send_button': False,
            'sending_email': False
        }
def initialize_camera_state():
    if 'camera_initialized' not in st.session_state:
        st.session_state.camera_initialized = False
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None
    if 'first_run' not in st.session_state:
        st.session_state.first_run = True

def main():
    initialize_email_settings()
    initialize_notification_state()
    initialize_camera_state()  # Add this line
    st.title("VESTIQUE - Smart Wardrobe Assistant")
    
    feature_extractor = FeatureExtractor()
    tracker = WardrobeTracker(feature_extractor)
    email_notifier = EmailNotifier()

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

        # Email Settings in Sidebar
        st.divider()
        st.subheader("📧 Email Settings")
        with st.expander("Configure Email"):
            sender_email = st.text_input(
                "Gmail Address", 
                value=st.session_state.sender_email,
                help="Enter the Gmail address you want to send notifications from"
            )
            
            email_password = st.text_input(
                "App Password", 
                type="password",
                value=st.session_state.email_password,
                help="Enter your Gmail App Password (Not your regular Gmail password). Get it from Google Account -> Security -> 2-Step Verification -> App passwords"
            )
            
            if st.button("Save Email Settings"):
                if '@gmail.com' not in sender_email:
                    st.error("Please enter a valid Gmail address")
                elif len(email_password) != 16:
                    st.error("App Password should be 16 characters. Please check your Google App Password")
                else:
                    st.session_state.sender_email = sender_email
                    st.session_state.email_password = email_password
                    st.session_state.email_configured = True
                    st.success("✅ Email settings saved!")

        # Default reset period
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
    tab1, tab2, tab3, tab4 = st.tabs(["Capture", "My Wardrobe", "Edit Wardrobe", "Notifications"])
    
    with tab1:
        
            st.subheader("Capture New Item" if mode == "Single Item" else "Capture Outfit")
            # Fix for first run
            if st.session_state.first_run:
                st.session_state.first_run = False
                st.rerun()
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
                image = Image.open(camera)
                st.session_state.current_image = image
                
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
                        try:
                            # Create a new event loop
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # Run the async operation
                            with st.spinner("Adding item to wardrobe..."):
                                success = loop.run_until_complete(
                                    tracker.add_new_item(
                                        image, 
                                        item_type,
                                        is_outfit=(mode == "Full Outfit"),
                                        name=name
                                    )
                                )
                                
                            if success:
                                st.success("✅ Added to wardrobe!")
                                
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
                        
                        finally:
                            # Clean up the event loop
                            try:
                                loop.close()
                            except:
                                pass
    
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
                            
                    current_wear_count = item.get('wear_count', 0)
                    new_wear_count = st.number_input(
                        "Times worn",
                        min_value=0,
                        value=int(current_wear_count),
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
                        success = tracker.update_item(
                            item['id'],
                            item['collection'],
                            datetime.combine(new_last_worn, datetime.min.time()).isoformat(),
                            new_wear_count
                        )
                        if success:
                            st.success("✅ Item updated!")
                            time.sleep(0.5)
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

    # In your main.py notifications tab
    # In your main.py, replace the notifications tab code with this:

    with tab4:
        st.subheader("📧 Email Notifications")
        
        recipient_email = st.text_input("Your Email Address")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("Check Unworn Items", use_container_width=True):
                st.write(f"Total items in database: {len(tracker.database['items'])}")
                unworn_items = email_notifier.check_unworn_items(tracker)
                st.session_state.notification_state['unworn_items'] = unworn_items
                st.session_state.notification_state['show_send_button'] = True
                
            # Display unworn items if they exist in session state
            if st.session_state.notification_state['unworn_items']:
                unworn_items = st.session_state.notification_state['unworn_items']
                st.warning(f"Found {len(unworn_items)} items unworn for 7+ days")
                
                with st.expander("View Unworn Items"):
                    for item in unworn_items:
                        st.write(f"• {item.get('name', item['type'])} - Last worn: {item['last_worn']}")
                
                if st.session_state.notification_state['show_send_button']:
                    send_col1, send_col2 = st.columns([3, 1])
                    with send_col1:
                        if st.button("📧 Send Reminder Email", use_container_width=True):
                            if not recipient_email:
                                st.error("Please enter your email address first")
                            else:
                                status_placeholder = st.empty()
                                progress_bar = st.progress(0)
                                
                                try:
                                    # Update progress
                                    status_placeholder.text("Generating email content...")
                                    progress_bar.progress(25)
                                    
                                    # Generate content first
                                    email_content = email_notifier.generate_personalized_content(unworn_items)
                                    
                                    # Show preview
                                    progress_bar.progress(50)
                                    status_placeholder.text("Sending email...")
                                    
                                    with st.expander("📧 Preview Generated Email"):
                                        st.text(email_content)
                                    
                                    # Send email
                                    success = email_notifier.send_notification(recipient_email, unworn_items)
                                    progress_bar.progress(100)
                                    
                                    if success:
                                        status_placeholder.success("✅ Email sent successfully!")
                                        st.balloons()
                                    else:
                                        status_placeholder.error("Failed to send email")
                                    
                                    # Keep status visible for a moment
                                    time.sleep(2)
                                    
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                finally:
                                    # Clean up progress elements
                                    progress_bar.empty()
            
            elif st.session_state.notification_state.get('unworn_items') == []:
                st.success("All items in your wardrobe are being used regularly!")
        
        with col2:
            if st.button("Send Test Email", use_container_width=True):
                if not recipient_email:
                    st.error("Please enter your email address first")
                else:
                    with st.spinner("Sending test email..."):
                        test_items = [{
                            "name": "Test Item",
                            "type": "T-Shirt",
                            "last_worn": datetime.now().isoformat(),
                            "wear_count": 1
                        }]
                        success = email_notifier.send_notification(recipient_email, test_items)
                        if success:
                            st.success("Test email sent!")
                            with st.expander("📧 Test Email Preview"):
                                st.text(email_notifier.generate_personalized_content(test_items))

if __name__ == "__main__":
    main()