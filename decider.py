import requests
LAM_API_KEY = 'b9e39db6-fe20-4a16-9803-385f77f309c3'
API_URL = 'https://api.sambanova.ai/v1/chat/completions'
HEADERS = {
    "Authorization": f"Bearer {LAM_API_KEY}",
    "Content-Type": "application/json"
}

def decide_preference(set_of_top_worn, set_of_least_worn, model='Meta-Llama-3.1-70B-Instruct'):
    data = {
        "stream": False,
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a highly intelligent fashion advisor and stylist with expertise in analyzing wardrobe data. Your task is to assist in optimizing wardrobe preferences based on usage data."
            },
            {
                "role": "user",
                "content": f"""Here is the data for the most worn and least worn clothing items in my wardrobe:

                ### Most Worn:
                {set_of_top_worn}

                ### Least Worn:
                {set_of_least_worn}

                Please analyze this data and return the following structured response:
                1. **Characteristics of Most Worn Items**: A list of common features (e.g., colors, materials, styles, use cases) that make these items popular.
                2. **Characteristics of Least Worn Items**: A list of common features that make these items less appealing or harder to use.
                3. **Overall Recommendation**: A concise suggestion for future wardrobe acquisitions based on the trends, addressing how to optimize for both practicality and style.

                ### Example Response Format:
                [
                    ["Characteristics of Most Worn Items"],
                    ["Characteristics of Least Worn Items"],
                    "Overall Recommendation"
                ]

                Your response must strictly adhere to this format without additional text or explanations.
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
    


