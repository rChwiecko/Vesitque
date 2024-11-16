import json
from datetime import datetime
from pathlib import Path
import streamlit as st
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import seaborn as sns
import cv2

class WardrobeTracker:
    def __init__(self, feature_extractor):
        self.feature_extractor = feature_extractor
        self.db_path = Path("clothing_database.json")
        self.similarity_threshold = 0.70
        self.database = self.load_database()

    def load_database(self):
        """Load or create database"""
        try:
            if self.db_path.exists():
                with open(self.db_path) as f:
                    return json.load(f)
            else:
                return {"items": []}
        except Exception as e:
            st.error(f"Error loading database: {str(e)}")
            return {"items": []}

    def save_database(self):
        """Save database to file"""
        try:
            with open(self.db_path, "w") as f:
                json.dump(self.database, f, indent=4)
        except Exception as e:
            st.error(f"Error saving database: {str(e)}")

    def find_matching_item(self, features):
        """Find matching item with debug info"""
        if features is None:
            return None, 0
            
        matches = []
        
        for item in self.database["items"]:
            try:
                stored_features = np.array(item["features"])
                similarity = self.feature_extractor.calculate_similarity(features, stored_features)
                matches.append({
                    "item": item,
                    "similarity": similarity
                })
            except Exception as e:
                st.warning(f"Error comparing with item {item.get('id', 'unknown')}: {str(e)}")
                continue
        
        # Sort by similarity
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Show debug info
        if matches:
            st.write("### Similarity Scores:")
            for match in matches[:3]:  # Show top 3 matches
                st.write(f"- Match score: {match['similarity']:.3f} for {match['item']['type']}")
            
            if matches[0]["similarity"] > self.similarity_threshold:
                return matches[0]["item"], matches[0]["similarity"]
        return None, 0

    def visualize_comparison(self, current_image, current_features, matching_item=None):
        """Visualize feature comparison between current and matched item"""
        st.write("## Feature Analysis")
        
        # Color Analysis
        st.write("### Color Comparison")
        img_np = np.array(current_image)
        
        # Extract dominant colors
        pixels = img_np.reshape(-1, 3)
        kmeans = KMeans(n_clusters=5, n_init=10)
        kmeans.fit(pixels)
        colors = kmeans.cluster_centers_.astype(int)
        
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4))
        
        # Current image histogram
        for i, color in enumerate(['r', 'g', 'b']):
            hist = cv2.calcHist([img_np], [i], None, [256], [0, 256])
            ax1.plot(hist, color=color, alpha=0.7, label=f'Current {color}')
        ax1.set_title("Color Distribution")
        ax1.legend()
        
        # Dominant colors
        for idx, color in enumerate(colors):
            ax2.add_patch(plt.Rectangle((idx, 0), 1, 1, color=color/255))
        ax2.set_xlim(0, len(colors))
        ax2.set_ylim(0, 1)
        ax2.set_title("Dominant Colors")
        
        # Feature comparison if there's a match
        if matching_item:
            stored_features = np.array(matching_item["features"])
            min_length = min(len(current_features), len(stored_features))
            
            # Normalize features for visualization
            scaler = MinMaxScaler()
            current_norm = scaler.fit_transform(current_features[:min_length].reshape(-1, 1)).flatten()
            stored_norm = scaler.transform(stored_features[:min_length].reshape(-1, 1)).flatten()
            
            # Plot feature differences
            diff = np.abs(current_norm - stored_norm)
            ax3.hist(diff, bins=50, color='blue', alpha=0.6)
            ax3.set_title("Feature Difference Distribution")
            ax3.axvline(diff.mean(), color='red', linestyle='--', label=f'Mean Diff: {diff.mean():.3f}')
            ax3.legend()
        
        st.pyplot(fig)
        
        self._show_pattern_analysis(img_np, current_features)
        self._show_matching_analysis(current_features, matching_item)

    def _show_pattern_analysis(self, img_np, current_features):
        st.write("### Pattern Recognition")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Edge Detection")
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            st.image(edges, caption="Detected Edges", use_column_width=True)
        
        with col2:
            st.write("Feature Heatmap")
            feature_length = len(current_features)
            map_size = int(np.sqrt(feature_length/4))
            
            try:
                feature_map = current_features[:map_size*map_size].reshape(map_size, map_size)
                fig, ax = plt.subplots()
                sns.heatmap(feature_map, ax=ax)
                ax.set_title("Feature Distribution")
                st.pyplot(fig)
            except Exception:
                st.write("Could not create feature heatmap")
                st.write(f"Feature length: {feature_length}")

    def _show_matching_analysis(self, current_features, matching_item):
        if matching_item:
            st.write("### Similarity Analysis")
            stored_features = np.array(matching_item["features"])
            min_length = min(len(current_features), len(stored_features))
            
            scaler = MinMaxScaler()
            current_norm = scaler.fit_transform(current_features[:min_length].reshape(-1, 1)).flatten()
            stored_norm = scaler.transform(stored_features[:min_length].reshape(-1, 1)).flatten()
            diff = np.abs(current_norm - stored_norm)
            
            col1, col2 = st.columns(2)
            
            with col1:
                matching_features = np.where(diff < diff.mean())[0]
                st.metric("Strong Matching Points", len(matching_features))
                st.metric("Similarity Score", f"{self.feature_extractor.calculate_similarity(current_features, stored_features):.3f}")
            
            with col2:
                corr = np.corrcoef(current_norm[:100], stored_norm[:100])[0,1]
                st.metric("Feature Correlation", f"{corr:.3f}")
                st.metric("Pattern Match", f"{(1 - diff.mean()):.3f}")
            
            self._show_feature_importance(current_features, stored_features)

    def _show_feature_importance(self, current_features, stored_features):
        st.write("### Feature Importance")
        feature_importance = np.abs(current_features - stored_features[:len(current_features)])
        top_n = 10
        top_indices = np.argsort(feature_importance)[-top_n:]
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(range(top_n), feature_importance[top_indices])
        ax.set_title(f"Top {top_n} Most Different Features")
        st.pyplot(fig)

    def process_image(self, image):
        """Process image with improved matching and visualization"""
        features = self.feature_extractor.extract_features(image)
        if features is None:
            return "error", None, 0
            
        matching_item, similarity = self.find_matching_item(features)

        if st.session_state.get('debug_mode', False):
            self.visualize_comparison(image, features, matching_item)

        if matching_item:
            last_worn = datetime.fromisoformat(matching_item["last_worn"])
            days_since_worn = (datetime.now() - last_worn).days
            
            st.write(f"Days since last worn: {days_since_worn}")
            
            if days_since_worn >= 2:
                matching_item["last_worn"] = datetime.now().isoformat()
                matching_item["days_unworn"] = 0
                self.save_database()
                return "existing", matching_item, similarity
            else:
                return "too_soon", matching_item, similarity
        return "new", None, 0