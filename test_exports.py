import urllib.request
import json
import os

pid = 'archi_35x65_modern_40109'
formats = ['svg', 'png', 'dxf', 'pdf', 'obj', 'blend']
results = {}

for fmt in formats:
    payload = json.dumps({
        'project_id': pid,
        'version': 2,
        'plot_width': 35.0,
        'plot_length': 65.0,
        'style': 'modern'
    }).encode('utf-8')
    req = urllib.request.Request(f'http://localhost:8000/api/export/{fmt}', data=payload, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    data = res.read()
    results[fmt] = {
        'status': res.getcode(),
        'bytes': len(data),
        'content_type': res.headers.get('Content-Type'),
        'disposition': res.headers.get('Content-Disposition')
    }

for k, v in results.items():
    print(f"[{k.upper()}] Status: {v['status']}, Size: {v['bytes']} bytes, File: {v['disposition']}")

