import requests

url = "https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/2026-03-01_anthem_index.json.gz"

resp = requests.head(url)
print(f"Status: {resp.status_code}")
print(f"File size: {int(resp.headers.get('Content-Length', 0)) / 1e9:.2f} GB")
print(f"Last modified: {resp.headers.get('Last-Modified', 'unknown')}")
