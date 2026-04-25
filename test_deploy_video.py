import urllib.request
import urllib.parse
from http.cookiejar import CookieJar
import json
import base64

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
data = urllib.parse.urlencode({'username': 'aialievich', 'password': 'password123'}).encode('utf-8')
req = urllib.request.Request("https://recc.roienv.com/login", data=data)
opener.open(req)

# Generate a fake valid tiny MP4 file (or just base64 garbage labeled as .mp4)
# We will use purely garbage so `cv2` will fail to read it.
# Actually, wait. If `cv2` fails to read, `ret` is False, and it logs an error!
b64_garbage = base64.b64encode(b"0" * 1000).decode('utf-8')

deploy_payload = {
    'app_id': '123',
    'app_secret': '123', # None to skip hash
    'access_token': '123',
    'ad_account_id': '123',
    'page_id': '123',
    'primary_text': 'Hello',
    'daily_budget': '10',
    'files_base64': [{'name': 'test.mp4', 'data': b64_garbage}]
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

