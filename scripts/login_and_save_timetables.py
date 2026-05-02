#!/usr/bin/env python3
import os
import sys
import urllib.parse
import urllib.request
import http.cookiejar

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(THIS_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

login_url = 'http://127.0.0.1:5000/login'
creds = {'username': 'superadmin', 'password': 'admin123'}

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

data = urllib.parse.urlencode(creds).encode()
req = urllib.request.Request(login_url, data=data)
try:
    resp = opener.open(req, timeout=10)
    # after login, fetch timetable pages
    urls = {
        'dept_1_sem_1': 'http://127.0.0.1:5000/timetable/?department_id=1&semester=1',
        'all_depts_sem_1': 'http://127.0.0.1:5000/timetable/?department_id=&semester=1',
        'dept_1_default': 'http://127.0.0.1:5000/timetable/?department_id=1',
    }
    # Add default views for departments 2..6 to verify default semester behavior
    for i in range(2, 7):
        urls[f'dept_{i}_default'] = f'http://127.0.0.1:5000/timetable/?department_id={i}'
    for name, url in urls.items():
        out_path = os.path.join(OUT_DIR, f"logged_{name}.html")
        try:
            r = opener.open(url, timeout=10)
            data = r.read()
            with open(out_path, 'wb') as f:
                f.write(data)
            print(f"Saved {url} -> {out_path} ({len(data)} bytes)")
        except Exception as e:
            print('Fetch failed for', url, e)
except Exception as e:
    print('Login failed:', e)
