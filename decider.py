import requests
LAM_API_KEY = '591a72d6-7705-4374-b3d9-1d528b17c5b3'
API_URL = 'https://api.sambanova.ai/v1/chat/completions'
HEADERS = {
    "Authorization": f"Bearer {LAM_API_KEY}",
    "Content-Type": "application/json"
}

def decide_preference(top_worn, least_worn, model='Meta-Llama-3.1-70B-Instruct'):
    data = {
        "stream": False,
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a highly intelligent fashion advisor and stylist with expertise in analyzing wardrobe data. Your task is to assist in optimizing wardrobe preferences based on usage data. Your response MUST strictly adhere to this format without additional text or explanations."
            },
            {
                "role": "user",
                "content": f"""Here is the data for the most worn and least worn clothing item in my wardrobe:

                ### Most Worn:
                {top_worn}

                ### Least Worn:
                {least_worn}

                Please analyze this data and return the following structured response:
                1. **Key Characteristics of Most Worn Item**: A list of common features (e.g., colors, materials, styles, use cases) that make the items popular.
                2. **Key Characteristics of Least Worn Item**: A list of common features that make the item less appealing or harder to use.
                3. **Overall Recommendation**: A concise suggestion for future wardrobe acquisitions based on the trends, addressing how to optimize for both practicality and style.

                ### Example Response Format:
                [
                    ["Characteristics of Most Worn Item"],
                    ["Characteristics of Least Worn Item"],
                    "Overall Recommendation"
                ]

                Your response MUST strictly adhere to this format without additional text or explanations and have ALL 3 parts stored in a list as the result
                """
            }
        ]
    }
    llama_res = requests.post(API_URL, headers=HEADERS, json=data)
    res_json = llama_res.json()
    print(res_json['choices'][0]['message']['content'])
    # Check if the request was successful
    
    if llama_res.status_code == 200:
        return res_json['choices'][0]['message']['content']  # Return the parsed JSON response
    else:
        raise Exception(f"Llama API Error {llama_res.status_code}: {llama_res.text}")
    


