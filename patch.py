import re

with open('static/script.js', 'r') as f:
    js = f.read()

# Replace the generic createProfile catch
js = re.sub(
    r'\.catch\(err => alert\("Network Error"\)\);',
    r'.catch(err => { console.error(err); alert("Network Error: " + err); });',
    js
)

# Fix switchProfile generic catch if any
js = re.sub(
    r'\.catch\(err => \{?\s*alert\("Network Error"\);?\s*\}?\);',
    r'.catch(err => { alert("Network Error: " + err); });',
    js
)

# Improve error reporting
js = js.replace(
    ".then(res => res.json())",
    ".then(async res => { const text = await res.text(); try { return JSON.parse(text); } catch(e) { throw new Error('Bad JSON: ' + text.substring(0,100)); } })"
)

with open('static/script.js', 'w') as f:
    f.write(js)
