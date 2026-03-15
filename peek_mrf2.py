import requests
import gzip

url = "https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/CA_AHPNMED0000_01_04.json.gz"

print("Scanning for CPT codes 99202-99215...")

TARGET_CODES = {"99202","99203","99204","99205",
                "99211","99212","99213","99214","99215","G2211"}

found_codes = set()

with requests.get(url, stream=True) as resp:
    resp.raise_for_status()
    d = gzip.GzipFile(fileobj=resp.raw)
    
    buffer = b""
    bytes_read = 0
    
    for chunk in iter(lambda: d.read(1024 * 1024), b""):
        buffer += chunk
        bytes_read += len(chunk)
        text = buffer.decode("utf-8", errors="ignore")
        
        for code in TARGET_CODES:
            if f'"billing_code":"{code}"' in text or f'"billing_code": "{code}"' in text:
                if code not in found_codes:
                    found_codes.add(code)
                    print(f"  Found CPT {code} at {bytes_read/1e9:.2f} GB")
        
        if len(found_codes) == len(TARGET_CODES):
            print("\nAll target CPT codes found!")
            break
            
        buffer = buffer[-1000:]
        
        if bytes_read % (100 * 1024 * 1024) < 1024 * 1024:
            print(f"  Scanned {bytes_read/1e9:.2f} GB, found {len(found_codes)}/{len(TARGET_CODES)} codes so far...")
        
        if bytes_read > 2 * 1024 * 1024 * 1024:
            print("\nStopped at 2GB")
            break

print(f"\nCPT codes found: {found_codes}")
print(f"CPT codes not found: {TARGET_CODES - found_codes}")


