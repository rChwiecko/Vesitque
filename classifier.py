import streamlit as st
from PIL import Image
import io
import google.generativeai as genai
import asyncio
import aiohttp
import requests
# Set your Gemini API key
GEMINI_API_KEY = 'AIzaSyC1BIQOOJ0TatPCGOtQIHiydLRv_xqTjDo'

#setting up SambaNova
LAM_API_KEY = 'b9e39db6-fe20-4a16-9803-385f77f309c3'
API_URL = 'https://api.sambanova.ai/v1/chat/completions'
HEADERS = {
    "Authorization": f"Bearer {LAM_API_KEY}",
    "Content-Type": "application/json"
}



# Initialize the Gemini API client
genai.configure(api_key=GEMINI_API_KEY)

# Streamlit app title
st.title("Image Analysis with Gemini API")

# File uploader for a single image
uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])


def prompt_llama(message, model="Meta-Llama-3.1-8B-Instruct", stream=False):
    headers = {
        "Authorization": f"Bearer {LAM_API_KEY}",
        "Content-Type": "application/json"
    }

    # Payload for the request
    data = {
        "stream": stream,
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": '''
                    You are a highly skilled fashion designer and software engineer tasked with analyzing clothing item descriptions and generating a detailed JSON schema describing their attributes. Your goal is to examine the clothing item description and create a structured JSON response with the following categories:
                    You are to ONLY generate the JSON text with NOTHING ELSE
                    The generated JSON MUST be syntatically correct, (example: all brackets are closed, commas in right places etc)
                    1. **Type**: The type of clothing (e.g., shirt, dress, pants, jacket).
                    2. **Material**: The material or fabric used (e.g., cotton, wool, polyester, denim).
                    3. **Color**:
                    - Primary Color: The dominant color of the clothing.
                    - Secondary Colors: Any additional colors or patterns (e.g., stripes, floral, polka dots).
                    4. **Fit and Style**:
                    - Fit: How the item fits (e.g., slim, loose, tailored, oversized).
                    - Style: The overall style (e.g., casual, formal, streetwear, vintage).
                    5. **Design Features**:
                    - Include notable design elements like collars, cuffs, buttons, zippers, embellishments, embroidery, logos, or unique stitching.
                    6. **Condition**: If visible, describe the condition (e.g., new, lightly worn, damaged).
                    7. **Brand or Label**: Include the brand name or logo if visible.
                    8. **Season**: Suggest the appropriate season for wearing the item (e.g., summer, winter, all-season).
                    9. **Use Case**: Suggest use cases for the clothing item (e.g., office wear, party wear, casual outing).
                    10. **Size and Dimensions** (if possible): Include any visible size labels or inferred dimensions (e.g., small, medium, large).

                    ### Example JSON Output:
                    ```json
                    {
                    "type": "jacket",
                    "material": "denim",
                    "color": {
                        "primary": "blue",
                        "secondary": ["white stitching"]
                    },
                    "fit_and_style": {
                        "fit": "regular",
                        "style": "casual"
                    },
                    "design_features": {
                        "collar": "classic fold-down",
                        "closures": ["metal buttons"],
                        "embellishments": ["distressed patches"],
                        "logo": "visible on pocket"
                    },
                    "condition": "lightly worn",
                    "brand": "Levi's",
                    "season": "all-season",
                    "use_case": ["casual outings", "layering"],
                    "size": "M"
                    }'''
            },
            {
                "role":"user",
                "content": message
            }
        ]
    }

    # Send the POST request asynchronously
    llama_res = requests.post(API_URL, headers=headers, json=data)
    res_json = llama_res.json()
    print(res_json['choices'][0]['message']['content'])
    # Check if the request was successful
    
    if llama_res.status_code == 200:
        return res_json['choices'][0]['message']['content']  # Return the parsed JSON response
    else:
        raise Exception(f"Llama API Error {llama_res.status_code}: {llama_res.text}")
    # async with aiohttp.ClientSession() as session:
    #     async with session.post(API_URL, headers=headers, json=data) as response:
    #         if response.status == 200:
    #             return await response
    #         else:
    #             error_text = await response.text()
    #             raise Exception(f"Error {response.status}: {error_text}")




async def analyze_image_gem(image_bytes):
    # Initialize the Gemini model
    gemini_model = genai.GenerativeModel(model_name='models/gemini-1.5-pro-001')

    # Generate content using the Gemini model
    response_gem = await gemini_model.generate_content_async(
        [image_bytes, '''You are a skilled fashion designer with extensive expertise in analyzing and describing clothing. You are presented with an image of a clothing item. Your task is to provide an in-depth, professional description of the item based on the image. 
            Consider the following aspects in your analysis:
            1. **Type of Clothing**: Specify whether it is a shirt, dress, pants, skirt, jacket, etc.
            2. **Material**: Identify the fabric type (e.g., cotton, polyester, wool, silk) and texture (e.g., smooth, coarse, stretchy).
            3. **Color and Pattern**: Describe the primary color, any additional colors, and patterns (e.g., floral, striped, plaid, solid).
            4. **Fit and Style**: Explain the fit (e.g., loose, slim, tailored) and the overall style (e.g., casual, formal, modern, vintage).
            5. **Design Features**: Highlight unique features, such as buttons, zippers, collars, cuffs, hems, embellishments, embroidery, or logos.
            6. **Condition**: If visible, assess the item's condition (e.g., new, lightly worn, damaged).
            7. **Brand or Label**: If there are visible labels, include the brand and any relevant details.

            Be as detailed as possible, using professional language suitable for a fashion catalog or critique. Begin your analysis with the clothing type and proceed through each aspect in a logical order. If certain details cannot be inferred from the image, acknowledge them explicitly.

            For example: "This is a slim-fit men's button-up shirt made of high-quality cotton. It features a classic plaid pattern with shades of navy blue and white. The material appears smooth and slightly breathable, suitable for semi-formal occasions. The shirt is styled with a sharp collar, pearl-style buttons, and adjustable cuffs. Based on the visible tag, it is a product of [Brand Name]."

            Now, analyze the image provided and deliver a comprehensive description of the clothing item.
        ''']
    )
    return str(response_gem.candidates[0].content.parts[0].text)


async def classify_outfit(image):
    response_gem = await (analyze_image_gem(image))
    response_lam = prompt_llama(response_gem)
    return response_lam

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
                res = asyncio.run(classify_outfit(image_final))
                st.write(res)
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload an image before clicking 'Analyze Image'.")
