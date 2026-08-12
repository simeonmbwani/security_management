import json
import urllib.request
import urllib.error

payload = json.dumps({
    'username': 'connectcheck',
    'password': 'StrongPass123!',
    'password_confirm': 'StrongPass123!',
    'first_name': 'Conn',
    'last_name': 'Check',
}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/api/auth/register/', data=payload, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print('status', resp.status)
        print(resp.read().decode()[:400])
except urllib.error.HTTPError as e:
    print('status', e.code)
    print(e.read().decode()[:400])
