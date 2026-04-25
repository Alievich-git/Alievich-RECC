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
    "Real estate investing"
]
for q in keywords:
    url = f"https://graph.facebook.com/v25.0/search?type=adTargetingCategory&class=interests&q={q}&access_token={token}&limit=10"
    res = requests.get(url).json()
    if 'data' in res:
        for item in res['data'][:3]:
            print(f"[{q}] -> ID: {item.get('id')}, Name: '{item.get('name')}'")
