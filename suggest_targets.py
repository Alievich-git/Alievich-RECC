import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("META_ACCESS_TOKEN")

seed_ids = ["6003446239080"]  # Property investing
interest_list = json.dumps(seed_ids)

print(f"=== Suggesting Valid Graph Nodes based on {seed_ids} ===")
url = f"https://graph.facebook.com/v25.0/search?type=adinterestsuggestion&interest_list={interest_list}&limit=50&access_token={token}"
res = requests.get(url).json()

if 'data' in res:
    for item in res['data']:
        lower = item.get('audience_size_lower_bound', item.get('audience_size', 'N/A'))
        print(f"SUGGESTION -> ID: {item.get('id')}, Name: '{item.get('name')}', Size: {lower}, Path: {item.get('path')}")
else:
    print("Error:", res)
