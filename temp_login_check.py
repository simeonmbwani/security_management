import json
import urllib.request

data = json.dumps({'username': 'simeonmbwani', 'password': '@A1n2d3y4.'}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login/', data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as res:
    print(res.status)
    print(res.read().decode())
