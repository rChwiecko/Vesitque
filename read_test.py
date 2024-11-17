import json

with open('clothing_database.json','r') as file:
    res = json.load(file)

print(res["items"][0])