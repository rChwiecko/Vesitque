import requests
from dotenv import load_dotenv
from pathlib import Path
import os
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
SAMBANOVA_API_KEY = os.environ["SAMBANOVA_API_KEY"]
API_URL = 'https://api.sambanova.ai/v1/chat/completions'
HEADERS = {
    "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
    "Content-Type": "application/json"
}

def decide_match(
    liked_characteristics, disliked_characteristics, item_characteristics, model='Meta-Llama-3.1-70B-Instruct'
):
    """
    Determines if an item matches a user's preferences based on their liked and disliked clothing characteristics.

    Args:
        liked_characteristics (list): A list of characteristics the user likes.
        disliked_characteristics (list): A list of characteristics the user dislikes.
        item_characteristics (list): A list of characteristics describing the clothing item.
        model (str): The model to use for evaluation.

    Returns:
        bool: True if the item matches the user's preferences, False otherwise.
    """

    # Define the prompt
    prompt = f"""
    You are a highly intelligent clothing stylist. Your task is to evaluate whether a clothing item matches a user's preferences.

    ### User Preferences:
    - **Liked Characteristics**: {liked_characteristics}
    - **Disliked Characteristics**: {disliked_characteristics}

    ### Item Characteristics:
    {item_characteristics}

    ### Instructions:
    - Return "True" if the item matches the user's preferences.
    - Return "False" if the item does not match the user's preferences.
    - An item matches the user's preferences if it has a significant overlap with the liked characteristics and avoids disliked characteristics.
    - Avoid providing explanations, additional text, or alternative outputs. Respond only with "True" or "False".

    ### Response Format:
    "True" or "False"
    """

    # Call the model (assuming you have a function to make the API call)
    data = {
        "stream": False,
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a highly intelligent clothing stylist tasked with evaluating clothing items based on user preferences. Strictly follow the response format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    # API request
    llama_res = requests.post(API_URL, headers=HEADERS, json=data)
    res_json = llama_res.json()

    # Validate and interpret the response
    if res_json and "choices" in res_json and res_json["choices"]:
        result = res_json["choices"][0]["message"]["content"].strip()
        if result == "True":
            return True
        elif result == "False":
            return False
        else:
            raise ValueError(f"Unexpected response from model: {result}")
    else:
        raise ValueError("No valid response from the model.")


