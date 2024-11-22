import os
import streamlit as st
import json
from openai import OpenAI

class DeveloperAssistant:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("SAMBANOVA_API_KEY"),
            base_url="https://api.sambanova.ai/v1"
        )
        
    def get_file_content(self, file_path):
        """Read and return the contents of a file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def get_completion(self, messages):
        """Get completion from the model."""
        try:
            response = self.client.chat.completions.create(
                model="Meta-Llama-3.1-70B-Instruct",
                messages=messages,
                temperature=0.5,
                max_tokens=700,
                top_p=0.9
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting response: {str(e)}"

def developer_assistant():
    st.title("👨‍💻 Developer Assistant")
    st.markdown("Select files to ask questions about your codebase.")

    # Initialize session state variables
    if 'dev_assistant' not in st.session_state:
        st.session_state.dev_assistant = DeveloperAssistant()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'code_contents' not in st.session_state:
        st.session_state.code_contents = ""
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = []
    if 'dev_input' not in st.session_state:
        st.session_state.dev_input = ""

    # List of file paths
    code_files = [
        "app.py",
        "capture_tab.py",
        "edit_wardrobe_tab.py",
        "marketplace_tab.py",
        "notifications_tab.py",
        "preferences_tab.py",
        "wardrobe_tracker.py",
        "style_advisor_tab.py",
        "feature_extractor.py"
    ]

    # File selection
    selected_files = st.multiselect("Choose files:", code_files)

    # Handle file selection changes
    if selected_files != st.session_state.selected_files:
        st.session_state.selected_files = selected_files
        
        if selected_files:
            # Read contents of selected files
            code_contents = []
            for file in selected_files:
                content = st.session_state.dev_assistant.get_file_content(file)
                code_contents.append(f"# File: {file}\n{content}")
            
            combined_code = "\n\n".join(code_contents)
            st.session_state.code_contents = combined_code
            
            # Reset conversation with new context
            system_message = {
                "role": "system",
                "content": f"""You are an expert software developer familiar with this codebase. 
                Here are the contents of the selected files:

                {combined_code}

                Analyze the code and help users understand it. Be specific and reference actual code when answering questions."""
            }
            st.session_state.messages = [system_message]
        else:
            st.session_state.code_contents = ""
            st.session_state.messages = []

    if selected_files:
        # Display code contents in expandable section
        with st.expander("Show selected code"):
            st.code(st.session_state.code_contents, language='python')

        # Display chat history
        for message in st.session_state.messages[1:]:  # Skip system message
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**Assistant:** {message['content']}")

        # Create columns for input and button
        col1, col2 = st.columns([5,1])
        
        # User input in first column
        with col1:
            user_input = st.text_input("Ask about the code:", key="dev_input_field")
        
        # Send button in second column
        with col2:
            send_pressed = st.button("Send", use_container_width=True)

        # Handle send button press
        if send_pressed and user_input:
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get response from assistant
            response = st.session_state.dev_assistant.get_completion(st.session_state.messages)
            
            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Force a rerun to update the display
            st.rerun()
    else:
        st.info("Please select at least one file to start the conversation.")

if __name__ == "__main__":
    developer_assistant()