import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
data = urllib.parse.urlencode({'username': 'aialievich', 'password': 'password123'}).encode('utf-8')
req = urllib.request.Request("https://recc.roienv.com/login", data=data)
try:
    resp = opener.open(req)
except Exception as e:
    resp = e

print("Login cookies:", cj)

# Create profile
data2 = urllib.parse.urlencode({'name': 'TestingProfileCLI'}).encode('utf-8')
req2 = urllib.request.Request("https://recc.roienv.com/api/create_profile", data=data2)
try:
    resp2 = opener.open(req2)
    print("Create profile body:", resp2.read().decode('utf-8'))
except Exception as e:
    print("Create fail:", e)

