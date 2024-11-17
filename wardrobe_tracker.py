from ui_components import WardrobeUI 
import json
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import json
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import cv2
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import seaborn as sns
from wardrobe_analysis import WardrobeAnalysis
import asyncio  # Add this
from classifier import classify_outfit  # Add this
class WardrobeTracker:
    def __init__(self, feature_extractor):
        self.feature_extractor = feature_extractor
        self.db_path = Path("clothing_database.json")
        self.similarity_threshold = 0.80
        self.reset_period = 7  # Days before an outfit can be worn again
        self.database = self.load_database()
        
        # Define clothing categories with emojis
        self.clothing_categories = {
            "T-Shirt": "👕",
            "Hoodie": "🧥",
            "Jacket": "🧥",
            "Pants": "👖",
            "Shorts": "🩳",
            "Dress": "👗",
            "Skirt": "👗",
            "Shoes": "👟",
            "Hat": "🧢",
            "Accessory": "👔",
            "Full Outfit": "👔"
        }
    def add_new_item_sync(self, image, item_type, is_outfit=False, name=None, existing_id=None):
        """Synchronous version of add_new_item for fallback"""
        features = self.feature_extractor.extract_features(image, is_full_outfit=is_outfit)
        if features is None:
            return False

        if existing_id is not None:
            # Add new view to existing item
            collection = "outfits" if is_outfit else "items"
            for item in self.database[collection]:
                if item['id'] == existing_id:
                    if 'reference_images' not in item:
                        item['reference_images'] = []
                        item['reference_features'] = []
                        item['reference_images'].append(item['image'])
                        item['reference_features'].append(item['features'])
                    
                    item['reference_images'].append(self.image_to_base64(image))
                    item['reference_features'].append(features.tolist())
                    self.save_database()
                    return True
            return False
        else:
            # Create new item with initial view and wear count
            collection = "outfits" if is_outfit else "items"
            
            new_item = {
                "id": len(self.database[collection]),
                "type": item_type,
                "name": name or item_type,
                "reference_images": [self.image_to_base64(image)],
                "reference_features": [features.tolist()],
                "last_worn": datetime.now().isoformat(),
                "image": self.image_to_base64(image),
                "features": features.tolist(),
                "reset_period": 7,
                "wear_count": 1
            }
            
            self.database[collection].append(new_item)
            self.save_database()
            return True
    def load_database(self):
        default_db = {
            "items": [],
            "outfits": []
        }
        
        try:
            if self.db_path.exists():
                with open(self.db_path) as f:
                    db = json.load(f)
                    if "outfits" not in db:
                        db["outfits"] = []
                    if "items" not in db:
                        db["items"] = []
                    return db
            else:
                return default_db
        except Exception as e:
            st.error(f"Error loading database: {str(e)}")
            return default_db

    def visualize_analysis(self, image, features, matching_item=None):
        """Visualize the analysis process in debug mode"""
        WardrobeAnalysis.visualize_analysis(image, features, matching_item, self.base64_to_image)
    async def add_new_item(self, image, item_type, is_outfit=False, name=None, existing_id=None):
        """Add new item or add view to existing item with wear count and AI analysis"""
        features = self.feature_extractor.extract_features(image, is_full_outfit=is_outfit)
        if features is None:
            return False

        if existing_id is not None:
            # Add new view to existing item
            collection = "outfits" if is_outfit else "items"
            for item in self.database[collection]:
                if item['id'] == existing_id:
                    if 'reference_images' not in item:
                        item['reference_images'] = []
                        item['reference_features'] = []
                        item['reference_images'].append(item['image'])
                        item['reference_features'].append(item['features'])
                    
                    item['reference_images'].append(self.image_to_base64(image))
                    item['reference_features'].append(features.tolist())
                    self.save_database()
                    return True
            return False
        else:
            # Create new item with initial view, wear count, and AI analysis
            collection = "outfits" if is_outfit else "items"
            
            # Convert image to RGB for analysis
            rgb_image = image.convert("RGB")
            
            try:
                # Get AI analysis
                description = await classify_outfit(rgb_image)
                
                new_item = {
                    "id": len(self.database[collection]),
                    "type": item_type,
                    "name": name or item_type,
                    "reference_images": [self.image_to_base64(image)],
                    "reference_features": [features.tolist()],
                    "last_worn": datetime.now().isoformat(),
                    "image": self.image_to_base64(image),
                    "features": features.tolist(),
                    "reset_period": 7,
                    "wear_count": 1,
                    "ai_analysis": description  # Add the AI analysis
                }
                
                self.database[collection].append(new_item)
                self.save_database()
                st.success("✅ Added to wardrobe with AI analysis!")
                return True
                
            except Exception as e:
                st.error(f"Error during AI analysis: {str(e)}")
                # Still add the item even if AI analysis fails
                new_item = {
                    "id": len(self.database[collection]),
                    "type": item_type,
                    "name": name or item_type,
                    "reference_images": [self.image_to_base64(image)],
                    "reference_features": [features.tolist()],
                    "last_worn": datetime.now().isoformat(),
                    "image": self.image_to_base64(image),
                    "features": features.tolist(),
                    "reset_period": 7,
                    "wear_count": 1
                }
                
                self.database[collection].append(new_item)
                self.save_database()
                st.warning("⚠️ Added to wardrobe, but AI analysis failed")
                return True
    
        # 4. Similarity Analysis (if there's a match)
        if matching_item is not None:
            st.write("### 🎯 Similarity Matching")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### Matched Item")
                if 'image' in matching_item:
                    matched_image = self.base64_to_image(matching_item['image'])
                    if matched_image:
                        st.image(matched_image, use_column_width=True)
                
            with col2:
                st.write("#### Similarity Metrics")
                stored_features = np.array(matching_item["features"])
                
                # Calculate various similarity metrics
                cosine_sim = self.feature_extractor.calculate_similarity(features, stored_features)
                feature_diff = np.abs(features - stored_features[:len(features)])
                diff_mean = feature_diff.mean()
                
                # Display metrics
                metrics = {
                    "Similarity Score": f"{cosine_sim:.3f}",
                    "Feature Match": f"{(1 - diff_mean):.3f}",
                    "Confidence": f"{max(0, min(1, cosine_sim)):.3f}"
                }
                
                for metric, value in metrics.items():
                    st.metric(metric, value)
                
                # Visualize feature differences
                fig, ax = plt.subplots()
                ax.hist(feature_diff, bins=50, color='blue', alpha=0.6)
                ax.set_title("Feature Differences Distribution")
                ax.axvline(diff_mean, color='red', linestyle='--', 
                          label=f'Mean Diff: {diff_mean:.3f}')
                ax.legend()
                st.pyplot(fig)

    def save_database(self):
        try:
            with open(self.db_path, "w") as f:
                json.dump(self.database, f, indent=4)
        except Exception as e:
            st.error(f"Error saving database: {str(e)}")

    def image_to_base64(self, image):
        """Convert PIL Image to base64 string"""
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85)  # Reduced quality for storage
        return base64.b64encode(buffered.getvalue()).decode()

    def base64_to_image(self, base64_string):
        """Convert base64 string back to PIL Image"""
        try:
            image_data = base64.b64decode(base64_string)
            return Image.open(BytesIO(image_data))
        except Exception as e:
            st.error(f"Error converting image: {str(e)}")
            return None

    def add_demo_data(self):
        """Add demo outfits with specific wear dates, reset periods, and wear counts"""
        sample_colors = [(200, 150, 150), (150, 200, 150), (150, 150, 200)]
        demo_outfits = []
        
        for i, (name, days_ago, reset_period, wear_count) in enumerate([
            ("Casual Friday", 4, 4, 3),
            ("Business Meeting", 6, 4, 2),
            ("Weekend Style", 2, 4, 5)
        ]):
            img = Image.new('RGB', (300, 400), sample_colors[i])
            
            demo_outfits.append({
                "id": i,
                "name": name,
                "type": "Full Outfit",
                "last_worn": (datetime.now() - timedelta(days=days_ago)).isoformat(),
                "features": [0] * 2048,
                "image": self.image_to_base64(img),
                "reset_period": reset_period,
                "wear_count": wear_count  # Add wear count to demo data
            })
        
        self.database["outfits"] = []
        self.database["outfits"].extend(demo_outfits)
        self.save_database()
        st.success("Demo data loaded successfully!")

    def display_wardrobe_grid(self):
        """Display wardrobe items using the UI components"""
        # Remove the st.write("## Your Wardrobe") line - let WardrobeUI handle the header
        
        # Combine items and outfits
        all_items = (
            [{"type": "item", **item} for item in self.database["items"]] +
            [{"type": "outfit", **outfit} for outfit in self.database["outfits"]]
        )
        
        def handle_add_view(item):
            st.session_state['adding_view_to'] = item['id']
            st.session_state['adding_view_type'] = 'outfit' if item.get('type') == 'Full Outfit' else 'item'
        
        def handle_capture(camera):
            image = Image.open(camera)
            success = self.add_new_item(
                image,
                item['type'],
                is_outfit=(st.session_state['adding_view_type'] == 'outfit'),
                existing_id=st.session_state['adding_view_to']
            )
            if success:
                st.success("✅ Added new view!")
                st.session_state.pop('adding_view_to')
                st.rerun()
        
        # Render the wardrobe grid
        WardrobeUI.render_wardrobe_grid(all_items, self.base64_to_image, handle_add_view)
        # Handle view addition modal if needed
        if 'adding_view_to' in st.session_state:
            for item in all_items:
                if item['id'] == st.session_state['adding_view_to']:
                    WardrobeUI.render_add_view_modal(item, handle_capture)
                    break

    def display_item_card(self, item):
        """Display a single item/outfit card with image and multi-view support"""
        with st.container():
            st.markdown("""
                <style>
                .clothing-card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 10px;
                    margin-bottom: 15px;
                }
                </style>
            """, unsafe_allow_html=True)
            
            emoji = self.clothing_categories.get(item.get('type', 'Other'), '👕')
            
            if 'image' in item:
                try:
                    image = self.base64_to_image(item['image'])
                    if image:
                        st.image(image, use_column_width=True)
                except Exception:
                    st.image("placeholder.png", use_column_width=True)
            
            st.markdown(f"### {emoji} {item.get('name', item['type'])}")
            
            # Display wear count
            wear_count = item.get('wear_count', 0)
            st.markdown(f"👕 Worn {wear_count} times")
            
            last_worn = datetime.fromisoformat(item["last_worn"])
            days_since = (datetime.now() - last_worn).days
            days_remaining = max(0, item.get('reset_period', 7) - days_since)
            
            st.warning(f"⏳ {days_remaining} days remaining")
            st.caption(f"Last worn: {last_worn.strftime('%Y-%m-%d')}")
            
            if 'reference_images' in item:
                num_views = len(item['reference_images'])
                st.caption(f"📸 {num_views} views of this item")
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Add View", key=f"add_view_{item['id']}"):
                    st.session_state['adding_view_to'] = item['id']
                    st.session_state['adding_view_type'] = 'outfit' if item.get('type') == 'Full Outfit' else 'item'
            
            if st.session_state.get('adding_view_to') == item['id']:
                camera = st.camera_input(
                    "Take another photo of this item",
                    key=f"camera_view_{item['id']}"
                )
                if camera:
                    image = Image.open(camera)
                    success = self.add_new_item(
                        image,
                        item['type'],
                        is_outfit=(st.session_state['adding_view_type'] == 'outfit'),
                        existing_id=item['id']
                    )
                    if success:
                        st.success("✅ Added new view!")
                        st.session_state.pop('adding_view_to')
                        st.rerun()


    def process_image(self, image, is_outfit=False):
        """Process image with correct wear count handling"""
        features = self.feature_extractor.extract_features(image, is_full_outfit=is_outfit)
        if features is None:
            return "error", None, 0

        if st.session_state.get('debug_mode', False):
            self.visualize_analysis(image, features)

        items_to_check = self.database["outfits"] if is_outfit else self.database["items"]
        matching_item = None
        best_similarity = 0

        for item in items_to_check:
            try:
                if 'reference_features' in item:
                    similarity = self.feature_extractor.calculate_similarity_multi_view(
                        features,
                        [np.array(f) for f in item['reference_features']]
                    )
                else:
                    stored_features = np.array(item["features"])
                    similarity = self.feature_extractor.calculate_similarity(features, stored_features)

                if similarity > self.similarity_threshold and similarity > best_similarity:
                    matching_item = item
                    best_similarity = similarity
            except Exception as e:
                st.warning(f"Error comparing items: {str(e)}")
                continue

        if matching_item:
            # Check if this is a new wear or just an update
            if not st.session_state.get('updating_item', False):
                # Only increment wear count if this is a new wear (not an update)
                matching_item["wear_count"] = matching_item.get("wear_count", 0) + 1
                matching_item["last_worn"] = datetime.now().isoformat()
            self.save_database()
            return "existing", matching_item, best_similarity

        return "new", None, 0

    
    def update_item(self, item_id, collection, new_last_worn, new_wear_count):
        """Properly update item details without incrementing wear count"""
        try:
            st.session_state['updating_item'] = True  # Flag to prevent wear count increment
            for item in self.database[collection]:
                if item['id'] == item_id:
                    item["last_worn"] = new_last_worn
                    item["wear_count"] = new_wear_count  # Directly set the wear count
                    item["reset_period"] = 7
                    self.save_database()
                    return True
        finally:
            st.session_state['updating_item'] = False  # Reset the flag
        return False