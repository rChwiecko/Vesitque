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
            .countdown {
                background: linear-gradient(90deg, #5D4037 0%, #8B6B61 50%, #5D4037 100%);
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
                margin: 0.5rem 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                color: rgba(255,255,255,0.9);
            }
            /* All other styles remain exactly the same */
            .hanger-bar {
                width: 100%;
                height: 48px;
                position: relative;
                margin: 0.5rem 0;
                background: linear-gradient(90deg, #5D4037 0%, #8B6B61 50%, #5D4037 100%);
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }

            /* Simplified image frame styling */
            .image-container {
                background: linear-gradient(45deg, #332420, #5C422F);
                padding: 10px;
                border-radius: 4px;
                margin: 0.5rem 0;
            }

            .image-container img {
                width: 100%;
                display: block;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 2px;
            }

            .hanger-bar svg {
                width: 100%;
                height: 100%;
                display: block;
            }

            .hanger-bar svg path {
                stroke: #3E2723;
                stroke-width: 2;
                fill: none;
            }

            /* Add new image frame styling */
            .image-wrapper {
                position: relative;
                padding: 12px;
                margin: 0.5rem 0;
                background: linear-gradient(45deg, 
                    #332420 0%,
                    #4A3428 25%,
                    #5C422F 50%,
                    #4A3428 75%,
                    #332420 100%
                );
                border-radius: 4px;
                box-shadow: 
                    inset 0 0 5px rgba(0,0,0,0.5),
                    0 2px 4px rgba(0,0,0,0.2);
            }

            .image-wrapper img {
                width: 100%;
                height: auto;
                display: block;
                border-radius: 2px;
            }

            /* Keep all other existing styles */
            .wardrobe-card {
                background-color: #1E1E1E;
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                position: relative;
                transition: transform 0.2s ease-in-out;
            }
            
            /* Keep existing gradient border effect */
            .wardrobe-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                border-radius: 12px;
                padding: 2px;
                background: linear-gradient(90deg, #3E2723 0%, #8B6B61 50%, #3E2723 100%);
                -webkit-mask: 
                    linear-gradient(#fff 0 0) content-box, 
                    linear-gradient(#fff 0 0);
                mask: 
                    linear-gradient(#fff 0 0) content-box, 
                    linear-gradient(#fff 0 0);
                -webkit-mask-composite: xor;
                mask-composite: exclude;
                pointer-events: none;
            }
            
            /* Keep all remaining styles exactly the same */
            .wardrobe-card:hover {
                transform: translateY(-2px);
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
                background: linear-gradient(90deg, #2C3E50 0%, #34495E 100%);
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.2s;
                width: 100%;
                margin-top: 0.5rem;
            }
            
            .action-button:hover {
                background: linear-gradient(90deg, #34495E 0%, #2C3E50 100%);
                transform: translateY(-1px);
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
    def render_wardrobe_grid(items, base64_to_image, on_add_view):
        """Render the updated wardrobe grid dynamically with precise column management"""
        WardrobeUI.render_card_container()  # Include necessary CSS styles
        
        # Render the title
        st.markdown("<h1>Your Wardrobe</h1>", unsafe_allow_html=True)
        
        if not items:
            st.info("👔 Your wardrobe is empty! Take some photos to get started.")
            return

        # Dynamically create a grid layout for all items
        num_items = len(items)
        num_columns = 3  # Set the number of columns in the grid
        rows = (num_items + num_columns - 1) // num_columns  # Calculate the number of rows needed

        for row in range(rows):
            # Create a new row of columns
            cols = st.columns(num_columns)

            for col_index in range(num_columns):
                item_index = row * num_columns + col_index

                # Ensure we only render existing items
                if item_index < num_items:
                    with cols[col_index]:
                        item = items[item_index]
                        WardrobeUI.render_item_card(item, base64_to_image, on_add_view)

    @staticmethod
    def render_item_card(item, base64_to_image, on_add_view):
        with st.container():
            hanger_svg = """
            <div class="hanger-bar">
                <svg viewBox="0 0 1000 60" preserveAspectRatio="none">
                <path d="M450 5 L450 15 Q450 20 500 20 Q550 20 550 15 L550 5" />
                <path d="M50 40 L450 40 Q500 40 550 40 L950 40" />
                <path d="M450 15 L50 40" stroke="#333" stroke-width="2" fill="none" />
                <path d="M550 15 L950 40" stroke="#333" stroke-width="2" fill="none" />
                </svg>
            </div>
            """
            st.markdown(hanger_svg, unsafe_allow_html=True)
            
            if 'image' in item:
                try:
                    image = base64_to_image(item['image'])
                    if image:
                        st.markdown(
                            f"""
                            <div class="image-container">
                                <img src="data:image/jpeg;base64,{item['image']}" alt="{item.get('name', item['type'])}">
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                except Exception:
                    st.image("placeholder.png", use_column_width=True)
            
            emoji = "🧥" if item.get('type') in ['Hoodie', 'Jacket'] else "👔"
            st.markdown(
                f'<div class="item-name">{emoji} {item.get("name", item["type"])}</div>', 
                unsafe_allow_html=True
            )
            
            last_worn = datetime.fromisoformat(item["last_worn"])
            days_since = (datetime.now() - last_worn).days
            days_remaining = max(0, item.get('reset_period', 7) - days_since)
            
            # Updated to use consistent brown gradient theme
            st.markdown(
                f"""
                <div class="countdown">
                    ⏳ {days_remaining} days remaining
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown(
                f'<div class="meta-info">Last worn: {last_worn.strftime("%Y-%m-%d")}</div>',
                unsafe_allow_html=True
            )
            
            if 'reference_images' in item:
                num_views = len(item['reference_images'])
                st.markdown(
                    f'<div class="view-count">📸 {num_views} views</div>',
                    unsafe_allow_html=True
                )
            
            button_key = f"add_view_{item['collection']}_{item['id']}_{hash(item['last_worn'])}"
            if st.button("📷 Add View", key=button_key):
                on_add_view(item['id'], item['collection'])



    @staticmethod
    def render_add_view_modal(item, on_capture):
        """Render the add view modal"""
        st.markdown("### 📸 Add New View")
        st.markdown(f"Adding another view for: **{item.get('name', item['type'])}**")
        
        camera = st.camera_input("Take another photo", key=f"camera_view_{item['id']}")
        if camera:
            on_capture(camera)