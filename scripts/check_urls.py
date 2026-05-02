#!/usr/bin/env python3
import urllib.request
urls = [
    'http://127.0.0.1:5000/timetable/?department_id=1&semester=1',
    'http://127.0.0.1:5000/timetable/?department_id=&semester=1',
]

for u in urls:
    try:
        with urllib.request.urlopen(u, timeout=10) as r:
            data = r.read()
            print(u)
            print('STATUS:', r.status)
            print('LENGTH:', len(data))
            print('-' * 60)
    except Exception as e:
        print(u)
        print('ERROR:', e)
        print('-' * 60)
