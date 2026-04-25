import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("META_ACCESS_TOKEN")

keywords = ["Real estate broker", "Luxury property", "Luxury real estate", "Real estate", "Air travel", "Business class", "investing"]
for q in keywords:
    print(f"\n=== Searching Ad Interests for: {q} ===")
    url = f"https://graph.facebook.com/v25.0/search?type=adinterest&q={q}&access_token={token}&limit=6"
    res = requests.get(url).json()
    if 'data' in res:
        for item in res['data']:
            lower = item.get('audience_size_lower_bound')
            if lower:
                print(f"ID: {item.get('id')}, Name: '{item.get('name')}', Size: {lower}")
