import streamlit as st

def initialize_email_settings():
    if 'email_configured' not in st.session_state:
        st.session_state.email_configured = False
        
    if 'sender_email' not in st.session_state:
        st.session_state.sender_email = ""
        
    if 'email_password' not in st.session_state:
        st.session_state.email_password = ""