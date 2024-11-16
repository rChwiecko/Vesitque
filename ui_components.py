import streamlit as st
from PIL import Image
from datetime import datetime
import base64

class WardrobeUI:
    @staticmethod
    def render_card_container():
        """Add CSS styling for the wardrobe cards"""
        st.markdown("""
            <style>
            .wardrobe-card {
                background-color: #1E1E1E;
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                border: 1px solid #333;
                transition: transform 0.2s ease-in-out;
            }
            
            .wardrobe-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            }
            
            .item-name {
                font-size: 1.5rem;
                font-weight: 600;
                margin: 0.5rem 0;
                color: white;
            }
            
            .countdown {
                background-color: #2C3333;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
                margin: 0.5rem 0;
            }
            
            .meta-info {
                color: #888;
                font-size: 0.8rem;
                margin-top: 0.5rem;
            }
            
            .view-count {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.9rem;
                color: #888;
                margin-top: 0.5rem;
            }
            
            .action-button {
                background-color: #2C3E50;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: background-color 0.2s;
                width: 100%;
                margin-top: 0.5rem;
            }
            
            .action-button:hover {
                background-color: #34495E;
            }

            .grid-container {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 1.5rem;
                padding: 1rem;
            }
            </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_item_card(item, base64_to_image, on_add_view):
        """Render a single wardrobe item card"""
        with st.container():
            st.markdown('<div class="wardrobe-card">', unsafe_allow_html=True)
            
            # Image
            if 'image' in item:
                try:
                    image = base64_to_image(item['image'])
                    if image:
                        st.image(image, use_column_width=True)
                except Exception:
                    st.image("placeholder.png", use_column_width=True)
            
            # Item name and emoji
            emoji = "🧥" if item.get('type') in ['Hoodie', 'Jacket'] else "👔"
            st.markdown(f'<div class="item-name">{emoji} {item.get("name", item["type"])}</div>', 
                       unsafe_allow_html=True)
            
            # Countdown
            last_worn = datetime.fromisoformat(item["last_worn"])
            days_since = (datetime.now() - last_worn).days
            days_remaining = max(0, item.get('reset_period', 7) - days_since)
            
            countdown_color = "#4A934A" if days_remaining == 0 else "#B4926A"
            st.markdown(
                f'<div class="countdown" style="background-color: {countdown_color}">'
                f'⏳ {days_remaining} days remaining</div>',
                unsafe_allow_html=True
            )
            
            # Last worn date
            st.markdown(
                f'<div class="meta-info">Last worn: {last_worn.strftime("%Y-%m-%d")}</div>',
                unsafe_allow_html=True
            )
            
            # View count
            if 'reference_images' in item:
                num_views = len(item['reference_images'])
                st.markdown(
                    f'<div class="view-count">📸 {num_views} views</div>',
                    unsafe_allow_html=True
                )
            
            # Add view button
            if st.button("📷 Add View", key=f"add_view_{item['id']}", 
                        help="Add another photo of this item to improve recognition"):
                on_add_view(item)
            
            st.markdown('</div>', unsafe_allow_html=True)

    @staticmethod
    def render_wardrobe_grid(items, base64_to_image, on_add_view):
        """Render the complete wardrobe grid"""
        WardrobeUI.render_card_container()
        
        if not items:
            st.info("👔 Your wardrobe is empty! Take some photos to get started.")
            return
        
        # Create responsive grid layout
        cols = st.columns(3)
        for idx, item in enumerate(items):
            with cols[idx % 3]:
                WardrobeUI.render_item_card(item, base64_to_image, on_add_view)

    @staticmethod
    def render_add_view_modal(item, on_capture):
        """Render the add view modal"""
        st.markdown("### 📸 Add New View")
        st.markdown(f"Adding another view for: **{item.get('name', item['type'])}**")
        
        camera = st.camera_input("Take another photo", key=f"camera_view_{item['id']}")
        if camera:
            on_capture(camera)