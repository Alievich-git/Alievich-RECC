import urllib.request
import urllib.parse
from http.cookiejar import CookieJar
import json

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
data = urllib.parse.urlencode({'username': 'aialievich', 'password': 'password123'}).encode('utf-8')
req = urllib.request.Request("https://recc.roienv.com/login", data=data)
opener.open(req)

# Deploy Campaign payload
deploy_payload = {
    'app_id': '123',
    'app_secret': '123',
    'access_token': '123',
    'ad_account_id': '123',
    'page_id': '123',
    'primary_text': 'Hello',
    'daily_budget': '10',
    'files_base64': [{'name': 'test.mp4', 'data': 'base64,AAAA'}]
}
req2 = urllib.request.Request("https://recc.roienv.com/api/deploy_campaign", data=json.dumps(deploy_payload).encode('utf-8'))
req2.add_header('Content-Type', 'application/json')

try:
    resp2 = opener.open(req2)
    print("Status:", resp2.getcode())
    print("Body:", resp2.read().decode('utf-8', errors='ignore'))
except Exception as e:
    print("Exception:", e)
    if hasattr(e, 'read'):
        print("Error Body:", e.read().decode('utf-8', errors='ignore'))

