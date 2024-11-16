import streamlit as st
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import cv2
from datetime import datetime
from feature_extractor import FeatureExtractor
from wardrobe_tracker import WardrobeTracker

def main():
    st.title("Smart Wardrobe Tracker")
    
    feature_extractor = FeatureExtractor()
    tracker = WardrobeTracker(feature_extractor)

    # Add debug mode toggle
    debug_mode = st.checkbox("Debug Mode (Show Feature Analysis)")
    st.session_state['debug_mode'] = debug_mode
    
    # Camera input
    camera = st.camera_input("Take a photo of what you're wearing")
    
    if camera:
        image = Image.open(camera)
        
        # Show preprocessing steps in debug mode
        if debug_mode:
            st.write("### Debug Information")
            st.write("Image preprocessing steps:")
            
            # Show detected region
            img_np = np.array(image)
            height, width = img_np.shape[:2]
            st.write(f"Image dimensions: {width}x{height}")
            
            # Show color histogram
            fig, ax = plt.subplots()
            for i, color in enumerate(['r', 'g', 'b']):
                hist = cv2.calcHist([img_np], [i], None, [256], [0, 256])
                ax.plot(hist, color=color)
            st.pyplot(fig)
        
        # Process image
        status, item, similarity = tracker.process_image(image)
        
        if status == "existing":
            st.success(f"✅ Found matching {item['type']}! (Similarity: {similarity:.3f})")
            if debug_mode:
                st.write("Match details:", item)
                
        elif status == "too_soon":
            st.warning(f"⚠️ You just wore this {item['type']} recently!")
            if debug_mode:
                st.write("Item details:", item)
                
        elif status == "new":
            st.info("🆕 New item detected!")
            clothing_type = st.selectbox(
                "What type of clothing is this?",
                ["Hoodie", "T-Shirt", "Jacket", "Other"]
            )
            
            if st.button("Add to Wardrobe"):
                features = feature_extractor.extract_features(image)
                if features is not None:
                    new_item = {
                        "id": len(tracker.database["items"]),
                        "type": clothing_type,
                        "features": features.tolist(),
                        "last_worn": datetime.now().isoformat(),
                        "days_unworn": 0
                    }
                    tracker.database["items"].append(new_item)
                    tracker.save_database()
                    st.success("✅ Added to wardrobe!")

    # Show wardrobe contents
    st.subheader("Your Wardrobe")
    for item in tracker.database["items"]:
        last_worn = datetime.fromisoformat(item["last_worn"])
        days_since = (datetime.now() - last_worn).days
        st.write(f"- {item['type']}: Last worn {days_since} days ago")

if __name__ == "__main__":
    main()