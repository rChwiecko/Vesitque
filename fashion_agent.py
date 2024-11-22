import streamlit as st
from decide_match import *
from SambaFit import *
def fashion_agent(tracker):
    st.title("🤖 SambaFit")
    
    st.markdown("Welcome to SambaFit! Ask me to create an outfit for the day!")

    model_data = []
    for item in tracker.database['items']:
        model_data.append({item['id']: item['ai_analysis']})

    # Chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display chat history
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        else:
            if isinstance(message["content"], list):  # If the bot's response contains images
                with st.container():
                    st.markdown("### Suggested Outfit")
                    cols = st.columns(len(message["content"]))  # Create columns for each image
                    for i, img_b64 in enumerate(message["content"]):
                        # Convert and display the image in separate columns
                        image = tracker.base64_to_image(img_b64)
                        cols[i].image(image, use_column_width=True)
            else:
                st.markdown(f"**SambaFit:** {message['content']}")

    # Callback function to process input
    def handle_input():
        # Retrieve user input
        user_input = st.session_state.get("unique_user_input", "")

        if user_input:
            # Add user's message to chat history
            st.session_state["messages"].append({"role": "user", "content": user_input})

            # Generate a response (placeholder for now)
            # Replace with API call to SambaFit AI when integrated
            response = generate_response(user_input, model_data)
            images_res = []
            for item in response:
                # Grab the key
                key = list(item.keys())[0]
                b64 = get_base_64_by_id(tracker, key)
                if b64 is not None:
                    images_res.append(b64)

            print(images_res)
            # Add the images to the bot's response in the chat
            st.session_state["messages"].append({"role": "bot", "content": images_res})

            # Display success message
            st.success("Response successfully updated with suggested outfits!")

            # Clear the input box
            st.session_state["unique_user_input"] = ""

    # User input box with a unique key
    st.text_input(
        "Type details here (weather, occasion etc):",
        key="unique_user_input",  # Ensure the key is unique
        on_change=handle_input,
    )



def get_base_64_by_id(tracker, id):
    for item in tracker.database['items']:
        if str(item["id"]) == id:
            return item['image']
    return None

def generate_response(user_input, data):
    print("data: ",data)
    model1_res = model1_tokenize_prompt(user_input)
    print("tokens: ", model1_res)
    overall_res = model2_select_items(model1_res, data)
    print("overall: ",overall_res)
    return overall_res