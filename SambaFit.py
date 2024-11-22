import requests
LAM_API_KEY = 'ba4070a0-299d-4e64-8952-0886808164b3'
API_URL = 'https://api.sambanova.ai/v1/chat/completions'
HEADERS = {
    "Authorization": f"Bearer {LAM_API_KEY}",
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
        list: A JSON array where each element is a dictionary of the form {"item description": item_id}.
    """
    data = {
        "stream": False,
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an intelligent assistant tasked with selecting wardrobe items based on user preferences and conditions. "
                    "Your response MUST strictly adhere to the specified format without additional text or explanations."
                )
            },
            {
                "role": "user",
                "content": f"""
                    Use the following tokens and database to identify suitable items:

                    ### Tokens:
                    {json.dumps(tokens)}

                    ### Database:
                    {json.dumps(database)}

                    ### Instructions:
                    Analyze the database. Select items where the AI analysis aligns with the tokens provided. 
                    Return the output in this format:
                    [
                        {{"<item_id>":"<item description>"}},
                        ...
                    ]
                    Do not include any additional text.

                    ### Example Response Format:
                    [
                        {{"101":"shirt"}},
                        {{"102":"pants"}}
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
