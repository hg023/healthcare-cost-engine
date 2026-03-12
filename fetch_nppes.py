"""
fetch_nppes.py
--------------
Builds a verified list of SF hospital NPIs.

Strategy for POC: start with a hardcoded seed list of known SF
hospital NPIs, then verify each one against the NPPES API to
confirm they are active and pull their full details.

This is more reliable than the NPPES search API for our use case.

Output: data/sf_hospitals.csv
"""

import requests
import pandas as pd
import os
import time

NPPES_API = "https://npiregistry.cms.hhs.gov/api/"
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "sf_hospitals.csv")

# Seed list of known SF hospital NPIs
# Sources: NPPES registry lookups, CMS hospital price transparency index
SF_HOSPITAL_NPIS = {
    # UCSF
    "1013150770": "UCSF Medical Center (Parnassus)",
    "1013243468": "UCSF Medical Center (Mt. Parnassus Box)",
    "1316194657": "UCSF Medical Center",
    "1952515975": "UCSF Medical Center at Mt. Zion",
    "1003062159": "UCSF Benioff Children's Hospital",
    # Zuckerberg SF General
    "1669471562": "Zuckerberg San Francisco General Hospital",
    # Sutter / CPMC
    "1740289176": "California Pacific Medical Center (CPMC) - Davies",
    "1154328526": "California Pacific Medical Center (CPMC) - Pacific",
    "1205834942": "California Pacific Medical Center (CPMC) - Mission Bernal",
    # Kaiser SF
    "1982621546": "Kaiser Foundation Hospital - San Francisco",
    # Saint Francis / Dignity Health
    "1003813882": "Saint Francis Memorial Hospital",
    # Saint Mary's
    "1528060608": "Saint Mary's Medical Center",
    # Chinese Hospital
    "1538161843": "Chinese Hospital",
    # Laguna Honda
    "1629071122": "Laguna Honda Hospital",
}


def lookup_npi(npi: str) -> dict:
    """Look up a single NPI and return its details."""
    params = {
        "version": "2.1",
        "number": npi,
    }
    resp = requests.get(NPPES_API, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    return results[0] if results else {}


def extract_fields(npi: str, label: str, result: dict) -> dict:
    """Extract the fields we care about from an NPPES result."""
    if not result:
        return {
            "npi": npi,
            "name": label,
            "address_1": "",
            "city": "",
            "state": "",
            "zip": "",
            "phone": "",
            "taxonomy_code": "",
            "taxonomy_desc": "",
            "status": "NOT FOUND",
        }

    basic = result.get("basic", {})
    addresses = result.get("addresses", [])
    taxonomies = result.get("taxonomies", [])

    address = next(
        (a for a in addresses if a.get("address_purpose") == "LOCATION"),
        addresses[0] if addresses else {}
    )

    primary_taxonomy = next(
        (t for t in taxonomies if t.get("primary")),
        taxonomies[0] if taxonomies else {}
    )

    return {
        "npi": npi,
        "name": basic.get("organization_name", label).strip(),
        "address_1": address.get("address_1", ""),
        "city": address.get("city", ""),
        "state": address.get("state", ""),
        "zip": address.get("postal_code", "")[:5],
        "phone": address.get("telephone_number", ""),
        "taxonomy_code": primary_taxonomy.get("code", ""),
        "taxonomy_desc": primary_taxonomy.get("desc", ""),
        "status": basic.get("status", ""),
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    records = []

    print(f"Verifying {len(SF_HOSPITAL_NPIS)} SF hospital NPIs against NPPES...\n")

    for npi, label in SF_HOSPITAL_NPIS.items():
        try:
            result = lookup_npi(npi)
            row = extract_fields(npi, label, result)
            status = row["status"]
            verified_name = row["name"]
            print(f"  {'OK  ' if status == 'A' else 'WARN'} {npi} | {verified_name} | {status}")
            records.append(row)
        except requests.RequestException as e:
            print(f"  ERR  {npi} | {label} | {e}")
        time.sleep(0.3)

    df = pd.DataFrame(records)
    active = df[df["status"] == "A"]

    print(f"\nVerified {len(active)} active SF hospitals out of {len(df)} checked")
    print(active[["npi", "name", "zip", "taxonomy_desc"]].to_string(index=False))

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
