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
                
                Please analyze these and provide:
                1. Common trends in both most worn and least worn items.
                2. Recommendations for improving wardrobe usage and optimization.
                3. Suggestions for integrating least worn items into more outfits.
                4. Suggestions for wardrobe acquisition based on the trends.

                The response should be of the form:
                    -Most worn characteristics
                    -Least worn characteristics
                
                KEEP THE RESPONSE BRIEF AND ONLY TALK ABOUT THE 2 POINTS ABOVE
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
    
best = [
{ "type": "blazer", "material": "polyester blend", "color": { "primary": "beige", "secondary": [] }, "fit_and_style": { "fit": "slightly relaxed", "style": "contemporary" }, "design_features": { "closure": "single-breasted with single button", "lapel": "notched", "sleeves": "long, cuffless" }, "condition": "new or like-new", "brand": "unknown", "season": "all-season", "use_case": ["professional settings", "casual outings"], "size": "unknown" }
]

worst = [
    { "type": "sweatshirt", "material": "cotton blend", "color": { "primary": "dark navy blue", "secondary": ["white graphic"] }, "fit_and_style": { "fit": "relaxed", "style": "casual" }, "design_features": { "collar": "hooded", "closures": ["drawstring"], "embellishments": ["graphic print"], "logo": "none" }, "condition": "new", "brand": "unknown", "season": "all-season", "use_case": ["travel", "casual outings"], "size": "unknown" }
]

print(decide_preference(best,worst))
