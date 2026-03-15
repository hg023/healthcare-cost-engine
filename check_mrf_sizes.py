import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.anthem.com/",
}

base_url = "https://anthembcca.mrf.bcbs.com/2026-03_720_27B0_in-network-rates_{}_of_24.json.gz"

for i in range(1, 4):
    part = str(i).zfill(2)
    url = base_url.format(part)
    resp = requests.head(url, headers=headers)
    size_gb = int(resp.headers.get('Content-Length', 0)) / 1e9
    print(f"Part {part}: {size_gb:.2f} GB — status {resp.status_code}")
    print(f"  Headers: {dict(resp.headers)}")