import requests
import json

url = 'http://localhost:8050/_dash-layout'
target_ids = ['chart-kem-ranking', 'chart-security-speed', 'chart-signature-comparison', 'chart-cloud-latency', 'chart-local-latency', 'chart-rsa-vs-mlkem']

def find_components(obj, ids, found):
    if isinstance(obj, dict):
        if obj.get('props', {}).get('id') in ids:
            found[obj['props']['id']] = obj.get('type')
        for key, value in obj.items():
            find_components(value, ids, found)
    elif isinstance(obj, list):
        for item in obj:
            find_components(item, ids, found)
    return found

try:
    response = requests.get(url)
    if response.status_code == 200:
        layout = response.json()
        results = find_components(layout, target_ids, {})
        print('--- COMPONENT TYPES ---')
        for component_id in target_ids:
            print(f"{component_id}: {results.get(component_id, 'Not Found')}")
except Exception as e:
    print(f"Error: {e}")
