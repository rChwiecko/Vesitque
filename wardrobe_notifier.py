from pathlib import Path
import streamlit as st
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
import json
import time

class EmailNotifier:
    def __init__(self):
        env_path = Path('.') / '.env'
        load_dotenv(dotenv_path=env_path)
        
        self.sender_email = os.getenv('GMAIL_ADDRESS')
        self.brevo_api_key = os.getenv('BREVO_API_KEY')
        self.sambanova_api_key = 'ba4070a0-299d-4e64-8952-0886808164b3'
        self.url = "https://api.sendinblue.com/v3/smtp/email"
        self.sambanova_url = "https://api.sambanova.ai/v1/chat/completions"

    def generate_personalized_content(self, items):
        """Generate personalized email content using SambaNova API"""
        try:
            progress_text = "Generating email content..."
            my_bar = st.progress(0, text=progress_text)
            
            # Prepare item information
            items_info = []
            for item in items:
                last_worn = datetime.fromisoformat(item['last_worn'])
                days_since = (datetime.now() - last_worn).days
                items_info.append({
                    'name': item.get('name', item['type']),
                    'type': item['type'],
                    'days_since': days_since,
                    'wear_count': item.get('wear_count', 0)
                })
            my_bar.progress(25, text="Processing items...")

            # SambaNova API request
            headers = {
                "Authorization": f"Bearer {self.sambanova_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""Write a personalized email about unworn clothing items. Be friendly and casual.

Items to mention:
{json.dumps(items_info, indent=2)}

Requirements:
1. Start with a warm greeting
2. For each item, mention how long it's been unworn
3. Suggest some creative ways to wear each item
4. Use emojis to keep it fun
5. End with an encouraging note
6. Keep it concise but friendly
"""

            payload = {
                "model": "Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {"role": "system", "content": "You are a friendly wardrobe assistant helping people make the most of their clothes."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "top_p": 0.9
            }

            my_bar.progress(50, text="Calling SambaNova API...")
            
            try:
                response = requests.post(
                    self.sambanova_url,
                    headers=headers,
                    json=payload,
                    timeout=30  # Add timeout
                )
                my_bar.progress(75, text="Processing response...")

                if response.status_code == 200:
                    content = response.json()['choices'][0]['message']['content']
                    my_bar.progress(100, text="Content generated!")
                    time.sleep(0.5)  # Give user time to see completion
                    my_bar.empty()
                    return content
                else:
                    st.error(f"SambaNova API error {response.status_code}")
                    my_bar.empty()
                    return self.get_fallback_content(items_info)
                
            except requests.exceptions.Timeout:
                st.error("SambaNova API timeout - using fallback content")
                my_bar.empty()
                return self.get_fallback_content(items_info)
            except Exception as e:
                st.error(f"SambaNova API error: {str(e)}")
                my_bar.empty()
                return self.get_fallback_content(items_info)
            
        except Exception as e:
            st.error(f"Error generating content: {str(e)}")
            return self.get_fallback_content(items_info)

    def send_notification(self, user_email, items):
        """Send email notification with pre-generated content"""
        if not user_email:
            st.error("Please enter your email address")
            return False
            
        try:
            # Generate content first
            email_content = self.generate_personalized_content(items)
            
            headers = {
                "accept": "application/json",
                "api-key": self.brevo_api_key,
                "content-type": "application/json"
            }
            
            payload = {
                "sender": {
                    "name": "Vestique",
                    "email": self.sender_email
                },
                "to": [{"email": user_email}],
                "subject": "💃 Time to Refresh Your Wardrobe!",
                "textContent": email_content
            }
            
            response = requests.post(
                self.url, 
                headers=headers, 
                json=payload, 
                timeout=10
            )
            
            return response.status_code == 201
            
        except Exception as e:
            st.error(f"Error sending email: {str(e)}")
            return False
    def check_unworn_items(self, wardrobe_tracker):
        """Check for items that haven't been worn in a while"""
        try:
            unworn_items = []
            current_time = datetime.now()
            
            # Debug print
            st.write(f"Checking {len(wardrobe_tracker.database['items'])} items...")
            
            for item in wardrobe_tracker.database["items"]:
                try:
                    last_worn = datetime.fromisoformat(item["last_worn"])
                    days_since = (current_time - last_worn).days
                    
                    st.write(f"Item {item.get('name', item['type'])}: {days_since} days since last worn")
                    
                    if days_since >= 7:  # Items unworn for 7+ days
                        unworn_items.append(item)
                        
                except Exception as e:
                    st.error(f"Error processing item {item.get('name', 'unnamed')}: {str(e)}")
                    continue
            
            st.write(f"Found {len(unworn_items)} unworn items")
            return unworn_items
            
        except Exception as e:
            st.error(f"Error in check_unworn_items: {str(e)}")
            return []
                    
        return unworn_items
    def generate_listing_content(self, item):
        """Generate marketplace listing content using SambaNova API"""
        try:
            progress_text = "Generating listing content..."
            my_bar = st.progress(0, text=progress_text)
            
            # Prepare item information
            item_info = {
                'name': item.get('name', item['type']),
                'type': item['type'],
                'condition': item.get('condition', 'Not specified'),
                'material': item.get('material', 'Not specified'),
                'color': item.get('color', {}).get('primary', 'Not specified'),
                'brand': item.get('brand', 'Not specified'),
                'wear_count': item.get('wear_count', 0)
            }
            
            my_bar.progress(25, text="Processing item details...")

            headers = {
                "Authorization": f"Bearer {self.sambanova_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""Create an engaging marketplace listing for this clothing item. 

    Item Details:
    {json.dumps(item_info, indent=2)}

    Requirements:
    1. Write a catchy title
    2. Create an engaging description
    3. Highlight key features and condition
    4. Suggest styling options
    5. Keep it professional but friendly
    6. Include emojis where appropriate
    """

            payload = {
                "model": "Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {"role": "system", "content": "You are a professional fashion marketplace listing creator."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "top_p": 0.9
            }

            my_bar.progress(50, text="Generating listing...")
            
            try:
                response = requests.post(
                    self.sambanova_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                my_bar.progress(75, text="Processing response...")

                if response.status_code == 200:
                    content = response.json()['choices'][0]['message']['content']
                    my_bar.progress(100, text="Listing generated!")
                    time.sleep(0.5)
                    my_bar.empty()
                    return content
                else:
                    st.error(f"SambaNova API error {response.status_code}")
                    my_bar.empty()
                    return None
                    
            except Exception as e:
                st.error(f"Error generating listing: {str(e)}")
                my_bar.empty()
                return None
                
        except Exception as e:
            st.error(f"Error in generate_listing_content: {str(e)}")
            return None