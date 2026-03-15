import requests
import gzip
import json

url = "https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/CA_ELRKMEDELRK.json.gz"

# Check size first
resp = requests.head(url)
print(f"Status: {resp.status_code}")
size_gb = int(resp.headers.get('Content-Length', 0)) / 1e9
print(f"File size: {size_gb:.2f} GB")
print(f"Last modified: {resp.headers.get('Last-Modified', 'unknown')}")

# Peek at first 500KB only
print("\nPeeking at first 500KB...")
headers = {"Range": "bytes=0-524288"}
resp = requests.get(url, headers=headers)

d = gzip.decompress(resp.content[:len(resp.content)])
text = d.decode("utf-8", errors="ignore")

# Print first 3000 characters
print(text[:3000])