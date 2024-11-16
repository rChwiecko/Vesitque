import streamlit as st
from PIL import Image
import io
import google.generativeai as genai
import asyncio

# Set your Gemini API key
GEMINI_API_KEY = 'AIzaSyDEVhn_pfoYX_ZhYctlQ42-hB5blT8TY0g'

# Initialize the Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# Streamlit app title
st.title("Image Analysis with Gemini API")

# File uploader for a single image
uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

async def analyze_image(image_bytes):
    # Initialize the Gemini model
    gemini_model = genai.GenerativeModel(model_name='models/gemini-1.5-pro-001')

    # Generate content using the Gemini model
    response = await gemini_model.generate_content_async(
        [image_bytes, "Analyze this image and describe it."]
    )
    return response

# Submit button
if st.button("Analyze Image"):
    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Convert image to bytes
        image_final = image.convert("RGB")

        # Run the async function to analyze the image
        try:
            with st.spinner("Analyzing image..."):
                response = asyncio.run(analyze_image(image_final))
                st.header("Analysis Results")
                st.write(response.text)
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload an image before clicking 'Analyze Image'.")
