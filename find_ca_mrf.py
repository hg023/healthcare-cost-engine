import requests
import gzip
import json
import re

url = "https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/2026-03-01_anthem_index.json.gz"

print("Streaming Anthem index to find CA files with plan names...")

ca_entries = []

with requests.get(url, stream=True) as resp:
    resp.raise_for_status()
    
    d = gzip.GzipFile(fileobj=resp.raw)
    
    buffer = b""
    chunk_size = 1024 * 1024
    bytes_read = 0
    
    for chunk in iter(lambda: d.read(chunk_size), b""):
        buffer += chunk
        bytes_read += len(chunk)
        
        text = buffer.decode("utf-8", errors="ignore")
        
        # Find CA file URLs - only anthembcca domain or /anthem/CA_ prefix
        matches = re.findall(
            r'(https://(?:anthembcca\.mrf\.bcbs\.com|antm-pt-prod[^"]*?/anthem/CA_)[^\s"]+\.json\.gz)',
            text
        )
        
        for url_found in matches:
            # Look back in buffer for plan_name near this URL
            url_pos = text.find(url_found)
            context = text[max(0, url_pos-500):url_pos+200]
            
            # Extract plan_name from context
            plan_match = re.search(r'"plan_name"\s*:\s*"([^"]+)"', context)
            plan_name = plan_match.group(1) if plan_match else "unknown"
            
            entry = {"url": url_found, "plan_name": plan_name}
            if entry not in ca_entries:
                ca_entries.append(entry)
                print(f"Found: {plan_name}")
                print(f"  URL: {url_found}")
        
        buffer = lines[-1].encode("utf-8") if (lines := text.split("\n")) else b""
        
        gb_read = bytes_read / 1e9
        if bytes_read % (100 * 1024 * 1024) < chunk_size:
            print(f"  Scanned {gb_read:.2f} GB, {len(ca_entries)} CA files found...")

print(f"\nTotal CA files found: {len(ca_entries)}")

# Save to file
with open(r"C:\Users\hinag\healthcare-cost-engine\data\anthem_ca_mrf_urls.txt", "w") as f:
    for entry in ca_entries:
        f.write(f"{entry['plan_name']}\t{entry['url']}\n")
print("Saved to data/anthem_ca_mrf_urls.txt")
