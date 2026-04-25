import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("META_ACCESS_TOKEN")

keywords = [
    "First class",
    "Business class", 
    "Penthouse",
    "Residential",
    "Townhouse",
    "Villa",
    "Luxury real estate"
]

for q in keywords:
    print(f"\n=== Searching Ad Interests for: {q} ===")
    url = f"https://graph.facebook.com/v25.0/search?type=adinterest&q={q}&access_token={token}&limit=15"
    res = requests.get(url).json()
    if 'data' in res:
        for item in res['data']:
            if item.get('audience_size_lower_bound') or item.get('audience_size'):
                lower = item.get('audience_size_lower_bound', item.get('audience_size'))
                upper = item.get('audience_size_upper_bound', 'N/A')
                print(f"VALID MATCH -> ID: {item.get('id')}, Name: '{item.get('name')}', Size: {lower} - {upper}")
    else:
        print("Error:", res)
