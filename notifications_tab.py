"""
notifications_tab.py

This module handles the email notifications functionality for the Vestique wardrobe assistant.
"""

import streamlit as st
import time
from datetime import datetime
from wardrobe_tracker import WardrobeTracker
from wardrobe_notifier import EmailNotifier

def notifications_tab(tracker: WardrobeTracker, email_notifier: EmailNotifier):
    """
    Implements the email notifications tab functionality.
    
    Args:
        tracker: WardrobeTracker instance for accessing wardrobe data
        email_notifier: EmailNotifier instance for handling notifications
    """
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