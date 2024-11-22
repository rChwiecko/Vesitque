import requests
import os
from dotenv import load_dotenv
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
SAMBANOVA_API_KEY = os.environ["SAMBANOVA_API_KEY"]
API_URL = 'https://api.sambanova.ai/v1/chat/completions'
HEADERS = {
    "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
    "Content-Type": "application/json"
}
import json

def model1_tokenize_prompt(prompt, model='Meta-Llama-3.1-70B-Instruct'):
    data = {
        "stream": False,
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an intelligent assistant tasked with extracting key tokens from user prompts related to wardrobe choices. "
                    "Your response MUST strictly adhere to the specified format without additional text or explanations."
                )
            },
            {
                "role": "user",
                "content": f"""
                    Analyze the following prompt and extract the following tokens:
                    1. Weather: The mentioned weather condition (e.g., warm, cold, rainy).
                    2. Occasion: The mentioned occasion (e.g., wedding, gym, casual outing).
                    3. Additional Preferences: Any specific preferences provided (e.g., color, style).

                    ### Prompt:
                    {prompt}

                    ### Example Response Format:
                    {{
                        "weather": "<extracted_weather>",
                        "occasion": "<extracted_occasion>",
                        "additional_preferences": "<extracted_additional_preferences>"
                    }}

                    Your response MUST strictly adhere to this format without additional text or explanations.
                """
            }
        ]
    }

    # Make the API request
    llama_res = requests.post(API_URL, headers=HEADERS, json=data)
    res_json = llama_res.json()

    # Check if the response is successful
    if llama_res.status_code == 200:
        try:
            # Return the parsed JSON response
            result = json.loads(res_json['choices'][0]['message']['content'])
            if isinstance(result, dict):
                return result
            else:
                raise ValueError("Response is not in the expected format.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
    else:
        raise Exception(f"Llama API Error {llama_res.status_code}: {llama_res.text}")



def model2_select_items(tokens, database, model='Meta-Llama-3.1-70B-Instruct'):
    """
    Selects items from the database based on tokens provided by Model 1 and returns a formatted list.

    Args:
        tokens (dict): Tokens extracted by Model 1 (weather, occasion, preferences).
        database (dict): A dictionary where keys are item IDs and values are AI analysis strings.
        model (str): The Llama model to use for the task.

    Returns:
        list: A JSON array where each element is a dictionary of the form {"item_id": "item description"}.
    """
    data = {
        "stream": False,
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an intelligent wardrobe assistant tasked with selecting appropriate clothing items from a database "
                    "based on user-provided tokens (e.g., weather, occasion, preferences). "
                    "Make lenient and adaptive decisions based on the clothing type and context. "
                    "Use logical reasoning to prioritize suitable clothing items, such as selecting pants over shorts for cold weather, "
                    "or selecting formal items for formal occasions. "
                    "IMPORTANT: Select only ONE item for each clothing type (e.g., one shirt, one pair of pants, one jacket, etc.). "
                    "Your response MUST strictly adhere to the specified JSON format."
                )
            },
            {
                "role": "user",
                "content": f"""
                    Use the following tokens and database to identify the most suitable clothing items:

                    ### Tokens:
                    {json.dumps(tokens)}

                    ### Database:
                    {json.dumps(database)}

                    ### Instructions:
                    - Analyze the database and match clothing items with the given tokens.
                    - Select only ONE item per clothing type (e.g., one shirt, one pair of pants, one jacket).
                    - Be flexible and adaptive in your choices. For example:
                        - Prioritize warm clothing (e.g., sweaters, jackets, pants) for cold weather.
                        - Choose lightweight and breathable clothing (e.g., t-shirts, shorts) for warm weather.
                        - Prioritize formal clothing (e.g., suits, dresses) for formal occasions.
                    - Consider additional preferences or requirements specified in the tokens.
                    - Avoid selecting multiple items of the same type (e.g., do not select two shirts or two pants).
                    - Ensure the selections complement each other to form a cohesive outfit.

                    Return the output in this JSON format:
                    [
                        {{"<item_id>": "<item description>"}},
                        ...
                    ]
                    Do not include any additional text or explanations.

                    ### Example Response Format:
                    [
                        {{"101": "shirt"}},
                        {{"102": "pants"}},
                        {{"103": "jacket"}}
                    ]
                """
            }
        ]
    }

    # Make the API request
    llama_res = requests.post(API_URL, headers=HEADERS, json=data)
    res_json = llama_res.json()

    # Check if the response is successful
    if llama_res.status_code == 200:
        try:
            # Return the parsed JSON array
            result = json.loads(res_json['choices'][0]['message']['content'])
            if isinstance(result, list):
                return result
            else:
                raise ValueError("Response is not in the expected format.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
    else:
        raise Exception(f"Llama API Error {llama_res.status_code}: {llama_res.text}")
