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
        st.write("## 🔍 Analysis Visualization")
        
        # 1. Image Preprocessing
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Original Image")
            st.image(image, use_column_width=True)
            
        with col2:
            st.write("### Edge Detection")
            img_np = np.array(image)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            st.image(edges, use_column_width=True)

        # 2. Color Analysis
        st.write("### 🎨 Color Analysis")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4))
        
        # Color histogram
        for i, color in enumerate(['r', 'g', 'b']):
            hist = cv2.calcHist([img_np], [i], None, [256], [0, 256])
            ax1.plot(hist, color=color, alpha=0.7, label=f'{color.upper()} Channel')
        ax1.set_title("Color Distribution")
        ax1.legend()
        
        # Dominant colors
        pixels = img_np.reshape(-1, 3)
        kmeans = KMeans(n_clusters=5, n_init=10)
        kmeans.fit(pixels)
        colors = kmeans.cluster_centers_.astype(int)
        
        # Plot dominant colors
        for idx, color in enumerate(colors):
            ax2.add_patch(plt.Rectangle((idx, 0), 1, 1, color=color/255))
        ax2.set_xlim(0, len(colors))
        ax2.set_ylim(0, 1)
        ax2.set_title("Dominant Colors")
        st.pyplot(fig)

        # 3. Feature Analysis
        st.write("### 🔢 Feature Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            # Feature heatmap
            feature_length = len(features)
            map_size = int(np.sqrt(feature_length/4))
            feature_map = features[:map_size*map_size].reshape(map_size, map_size)
            
            fig, ax = plt.subplots()
            sns.heatmap(feature_map, ax=ax)
            ax.set_title("Feature Distribution")
            st.pyplot(fig)
            
        with col2:
            # Feature importance visualization
            st.write("Top Feature Intensities")
            top_n = 10
            top_indices = np.argsort(np.abs(features))[-top_n:]
            top_values = features[top_indices]
            
            fig, ax = plt.subplots()
            ax.bar(range(top_n), top_values)
            ax.set_title("Top Feature Values")
            st.pyplot(fig)
    def add_new_item(self, image, item_type, is_outfit=False, name=None, existing_id=None):
        """Add new item or add view to existing item"""
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
                        # Move original image and features to lists
                        item['reference_images'].append(item['image'])
                        item['reference_features'].append(item['features'])
                    
                    # Add new view
                    item['reference_images'].append(self.image_to_base64(image))
                    item['reference_features'].append(features.tolist())
                    self.save_database()
                    return True
            return False
        else:
            # Create new item with initial view
            collection = "outfits" if is_outfit else "items"
            new_item = {
                "id": len(self.database[collection]),
                "type": item_type,
                "name": name or item_type,
                "reference_images": [self.image_to_base64(image)],
                "reference_features": [features.tolist()],
                "last_worn": datetime.now().isoformat(),
                "image": self.image_to_base64(image),  # Keep one as primary for display
                "features": features.tolist(),  # Keep one as primary for quick matching
                "reset_period": 7
            }
            
            self.database[collection].append(new_item)
            self.save_database()
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
        """Add demo outfits with specific wear dates and reset periods"""
        sample_colors = [(200, 150, 150), (150, 200, 150), (150, 150, 200)]
        demo_outfits = []
        
        for i, (name, days_ago, reset_period) in enumerate([
            ("Casual Friday", 4, 4),
            ("Business Meeting", 6, 4),
            ("Weekend Style", 2, 4)
        ]):
            img = Image.new('RGB', (300, 400), sample_colors[i])
            
            demo_outfits.append({
                "id": i,
                "name": name,
                "type": "Full Outfit",
                "last_worn": (datetime.now() - timedelta(days=days_ago)).isoformat(),
                "features": [0] * 2048,
                "image": self.image_to_base64(img),
                "reset_period": reset_period  # Add custom reset period
            })
        
        self.database["outfits"] = []
        self.database["outfits"].extend(demo_outfits)
        self.save_database()
        st.success("Demo data loaded successfully!")

    def display_wardrobe_grid(self):
        """Display wardrobe items in a grid with days remaining"""
        st.write("## Your Wardrobe")
        
        # Combine items and outfits
        all_items = (
            [{"type": "item", **item} for item in self.database["items"]] +
            [{"type": "outfit", **outfit} for outfit in self.database["outfits"]]
        )
        
        if not all_items:
            st.info("Your wardrobe is empty! Take some photos to get started.")
            return
            
        # Create columns for grid display
        cols = st.columns(3)
        
        for idx, item in enumerate(all_items):
            col = cols[idx % 3]
            with col:
                self.display_item_card(item)

    def display_item_card(self, item):
        """Display a single item/outfit card with image and multi-view support"""
        with st.container():
            # Add card styling
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
            
            # Get emoji for item type
            emoji = self.clothing_categories.get(item.get('type', 'Other'), '👕')
            
            # Display primary image
            if 'image' in item:
                try:
                    image = self.base64_to_image(item['image'])
                    if image:
                        st.image(image, use_column_width=True)
                except Exception:
                    st.image("placeholder.png", use_column_width=True)
            
            # Display item name with emoji
            st.markdown(f"### {emoji} {item.get('name', item['type'])}")
            
            # Calculate and display countdown
            last_worn = datetime.fromisoformat(item["last_worn"])
            days_since = (datetime.now() - last_worn).days
            days_remaining = max(0, item.get('reset_period', 7) - days_since)
            
            # Show countdown warning
            st.warning(f"⏳ {days_remaining} days remaining")
            st.caption(f"Last worn: {last_worn.strftime('%Y-%m-%d')}")
            
            # Add view counter if item has multiple views
            if 'reference_images' in item:
                num_views = len(item['reference_images'])
                st.caption(f"📸 {num_views} views of this item")
            
            # Add button for new views
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Add View", key=f"add_view_{item['id']}"):
                    st.session_state['adding_view_to'] = item['id']
                    st.session_state['adding_view_type'] = 'outfit' if item.get('type') == 'Full Outfit' else 'item'
            
            # Handle view addition if in progress
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
        """Enhanced image processing with multi-view matching"""
        features = self.feature_extractor.extract_features(image, is_full_outfit=is_outfit)
        if features is None:
            return "error", None, 0
            
        items_to_check = self.database["outfits"] if is_outfit else self.database["items"]
        matching_item = None
        best_similarity = 0
        
        for item in items_to_check:
            try:
                # Check if item has multiple reference features
                if 'reference_features' in item:
                    similarity = self.feature_extractor.calculate_similarity_multi_view(
                        features, 
                        [np.array(f) for f in item['reference_features']]
                    )
                else:
                    # Fallback to single feature comparison
                    stored_features = np.array(item["features"])
                    similarity = self.feature_extractor.calculate_similarity(features, stored_features)
                
                if similarity > self.similarity_threshold and similarity > best_similarity:
                    matching_item = item
                    best_similarity = similarity
            except Exception as e:
                st.warning(f"Error comparing items: {str(e)}")
                continue

        if matching_item:
            matching_item["last_worn"] = datetime.now().isoformat()
            matching_item["reset_period"] = 7
            self.save_database()
            return "existing", matching_item, best_similarity
                
        return "new", None, 0
    
    def update_item_reset_period(self, item_id, new_reset_period, collection="items"):
        """Update an item's reset period"""
        for item in self.database[collection]:
            if item['id'] == item_id:
                item['reset_period'] = new_reset_period
                self.save_database()
                return True
        return False