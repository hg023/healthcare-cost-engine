import requests
import os

url = "https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/CA_AHPNMED0000_01_04.json.gz"
output = r"C:\Users\hinag\healthcare-cost-engine\data\CA_AHPNMED0000_01_04.json.gz"

def download_with_resume(url, output):
    # Check existing file size for resume
    existing = os.path.getsize(output) if os.path.exists(output) else 0
    
    if existing > 0:
        print(f"Resuming download from {existing/1e9:.2f} GB...")
    
    headers = {"Range": f"bytes={existing}-"} if existing else {}
    
    with requests.get(url, stream=True, headers=headers, timeout=60) as resp:
        if resp.status_code == 416:
            print("File already fully downloaded.")
            return
        resp.raise_for_status()
        
        total = int(resp.headers.get('Content-Length', 0)) + existing
        downloaded = existing
        
        mode = 'ab' if existing else 'wb'
        with open(output, mode) as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = downloaded / total * 100 if total else 0
                    gb = downloaded / 1e9
                    print(f"\r  {gb:.2f} GB / {total/1e9:.2f} GB ({pct:.1f}%)", end="", flush=True)

while True:
    try:
        download_with_resume(url, output)
        print(f"\n\nDownload complete!")
        print(f"File size: {os.path.getsize(output)/1e9:.2f} GB")
        break
    except Exception as e:
        print(f"\nConnection dropped: {e}")
        print("Retrying in 30 seconds...")
        import time
        time.sleep(30)