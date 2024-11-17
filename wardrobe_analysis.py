import streamlit as st
import cv2
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import seaborn as sns
import numpy as np

class WardrobeAnalysis:
    @staticmethod
    def visualize_analysis(image, features, matching_item=None, base64_to_image=None):
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

        # 4. Similarity Analysis (if there's a match)
        if matching_item is not None:
            st.write("### 🎯 Similarity Matching")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("#### Matched Item")
                if 'image' in matching_item:
                    matched_image = base64_to_image(matching_item['image'])
                    if matched_image:
                        st.image(matched_image, use_column_width=True)
                
            with col2:
                st.write("#### Similarity Metrics")
                stored_features = np.array(matching_item["features"])
                
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