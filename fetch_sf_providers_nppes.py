import requests
import pandas as pd
import time

NPPES_API = "https://npiregistry.cms.hhs.gov/api/"
OUTPUT_FILE = r"C:\Users\hinag\healthcare-cost-engine\data\sf_providers_nppes.csv"

SF_ZIPS = [
    "94102", "94103", "94104", "94105", "94107", "94108", "94109", "94110",
    "94111", "94112", "94114", "94115", "94116", "94117", "94118", "94121",
    "94122", "94123", "94124", "94127", "94129", "94130", "94131", "94132",
    "94133", "94134", "94158", "94188"
]

TAXONOMIES = {
    "207Q00000X": "Family Medicine",
    "207QA0505X": "Adult Medicine",
    "207QG0300X": "Geriatric Medicine",
    "208D00000X": "General Practice",
    "207R00000X": "Internal Medicine",
    "207RG0300X": "Geriatric Medicine",
}

def fetch_batch(taxonomy_desc, zip_code, skip=0):
    params = {
        "version": "2.1",
        "enumeration_type": "NPI-1",
        "taxonomy_description": taxonomy_desc,
        "postal_code": zip_code,
        "state": "CA",
        "limit": 200,
        "skip": skip,
    }
    try:
        resp = requests.get(NPPES_API, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", []), data.get("result_count", 0)
    except requests.RequestException as e:
        print(f"  API error: {e}")
        return [], 0

def parse_provider(r):
    basic = r.get("basic", {})
    addresses = r.get("addresses", [])
    taxonomies = r.get("taxonomies", [])

    practice = {}
    for a in addresses:
        if a.get("address_purpose") == "LOCATION":
            practice = a
            break

    primary_taxonomy = {}
    for t in taxonomies:
        if t.get("primary"):
            primary_taxonomy = t
            break

    return {
        "npi": r.get("number"),
        "first_name": basic.get("first_name", ""),
        "last_name": basic.get("last_name", ""),
        "credential": basic.get("credential", ""),
        "gender": basic.get("gender", ""),
        "address": practice.get("address_1", ""),
        "city": practice.get("city", ""),
        "state": practice.get("state", ""),
        "zip": practice.get("postal_code", "")[:5],
        "phone": practice.get("telephone_number", ""),
        "taxonomy_code": primary_taxonomy.get("code", ""),
        "taxonomy_desc": primary_taxonomy.get("desc", ""),
    }

def main():
    all_providers = []

    for code, desc in TAXONOMIES.items():
        print(f"\nFetching: {desc}")
        total = 0
        for zip_code in SF_ZIPS:
            skip = 0
            while True:
                results, count = fetch_batch(desc, zip_code, skip)
                if not results:
                    break
                for r in results:
                    all_providers.append(parse_provider(r))
                total += len(results)
                if skip + len(results) >= count:
                    break
                skip += 200
                time.sleep(0.3)
        print(f"  Found {total} records across all SF zips")

    df = pd.DataFrame(all_providers)
    df = df.drop_duplicates(subset=["npi"])

    print(f"\nTotal unique SF primary care providers: {len(df)}")
    print(df.head(10).to_string())

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()