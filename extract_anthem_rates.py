import ijson
import gzip
import sqlite3
import pandas as pd
import pickle
import os

LOCAL_FILE = r"C:\Users\hinag\healthcare-cost-engine\data\CA_AHPNMED0000_01_04.json.gz"
PROVIDERS_FILE = r"C:\Users\hinag\healthcare-cost-engine\data\sf_providers_clean.csv"
DB_FILE = r"C:\Users\hinag\healthcare-cost-engine\data\anthem_rates.db"
LOOKUP_FILE = r"C:\Users\hinag\healthcare-cost-engine\data\group_lookup.pkl"

TARGET_CPT_CODES = {
    "99202", "99203", "99204", "99205",
    "99211", "99212", "99213", "99214", "99215",
    "G2211"
}

# Load SF provider NPIs
print("Loading SF providers...")
df = pd.read_csv(PROVIDERS_FILE, dtype=str)
sf_npis = set(df["npi"].dropna().tolist())
print(f"  {len(sf_npis)} SF provider NPIs loaded")

# Set up SQLite database
print("Setting up database...")
conn = sqlite3.connect(DB_FILE)
conn.execute("DROP TABLE IF EXISTS rates")
conn.execute("""
    CREATE TABLE rates (
        npi TEXT,
        cpt_code TEXT,
        network_name TEXT,
        negotiated_rate REAL,
        negotiated_type TEXT,
        billing_class TEXT,
        expiration_date TEXT
    )
""")
conn.commit()

# Pass 1 - Build provider group lookup
if os.path.exists(LOOKUP_FILE):
    print("\nPass 1: Loading saved group lookup from disk...")
    with open(LOOKUP_FILE, "rb") as f:
        data = pickle.load(f)
    group_to_npis = data["group_to_npis"]
    npi_to_groups = data["npi_to_groups"]
    print(f"  Loaded {len(group_to_npis)} groups, {len(npi_to_groups)} SF providers")
else:
    print("\nPass 1: Building provider group lookup from local file...")
    group_to_npis = {}
    npi_to_groups = {}
    count = 0

    with open(LOCAL_FILE, "rb") as f:
        raw = gzip.GzipFile(fileobj=f)
        parser = ijson.items(raw, "provider_references.item")

        for ref in parser:
            group_id = ref.get("provider_group_id")
            network_names = ref.get("network_name", [])
            provider_groups = ref.get("provider_groups", [])

            npis_in_group = []
            for pg in provider_groups:
                for npi in pg.get("npi", []):
                    npis_in_group.append(str(npi))

            sf_npis_in_group = [n for n in npis_in_group if n in sf_npis]

            if sf_npis_in_group:
                group_to_npis[group_id] = {
                    "npis": sf_npis_in_group,
                    "network_names": network_names
                }
                for npi in sf_npis_in_group:
                    if npi not in npi_to_groups:
                        npi_to_groups[npi] = []
                    npi_to_groups[npi].append(group_id)

            count += 1
            if count % 100000 == 0:
                print(f"  Processed {count:,} groups, {len(group_to_npis)} match SF providers...")

    print(f"\nPass 1 complete:")
    print(f"  Total groups scanned: {count:,}")
    print(f"  Groups with SF providers: {len(group_to_npis)}")
    print(f"  SF providers found: {len(npi_to_groups)}")

    print("Saving lookup to disk...")
    with open(LOOKUP_FILE, "wb") as f:
        pickle.dump({"group_to_npis": group_to_npis, "npi_to_groups": npi_to_groups}, f)
    print("  Saved.")

if len(npi_to_groups) == 0:
    print("\nNo SF providers found. Stopping.")
    conn.close()
    exit()

# Pass 2 - Extract rates
print("\nPass 2: Extracting rates for SF providers...")

target_group_ids = set(group_to_npis.keys())
rates_found = 0
batch = []

with open(LOCAL_FILE, "rb") as f:
    raw = gzip.GzipFile(fileobj=f)
    parser = ijson.items(raw, "in_network.item")
    cpt_count = 0

    for item in parser:
        billing_code = item.get("billing_code", "")
        billing_code_type = item.get("billing_code_type", "")

        if billing_code not in TARGET_CPT_CODES:
            continue
        if billing_code_type not in ("CPT", "HCPCS"):
            continue

        cpt_count += 1
        print(f"  Found CPT {billing_code}")

        for rate_obj in item.get("negotiated_rates", []):
            provider_refs = rate_obj.get("provider_references", [])
            matching_groups = [r for r in provider_refs if r in target_group_ids]

            if not matching_groups:
                continue

            for price in rate_obj.get("negotiated_prices", []):
                if price.get("negotiated_type") not in ("negotiated", "fee schedule"):
                    continue
                if price.get("billing_class") not in ("professional", "both"):
                    continue

                for group_id in matching_groups:
                    group_info = group_to_npis[group_id]
                    for npi in group_info["npis"]:
                        batch.append((
                            npi,
                            billing_code,
                            ", ".join(group_info["network_names"]),
                            float(price.get("negotiated_rate") or 0),
                            price.get("negotiated_type"),
                            price.get("billing_class"),
                            price.get("expiration_date"),
                        ))
                        rates_found += 1

        if len(batch) >= 1000:
            conn.executemany("INSERT INTO rates VALUES (?,?,?,?,?,?,?)", batch)
            conn.commit()
            batch = []
            print(f"  Saved {rates_found:,} rates so far...")

if batch:
    conn.executemany("INSERT INTO rates VALUES (?,?,?,?,?,?,?)", batch)
    conn.commit()

print(f"\nExtraction complete!")
print(f"  CPT codes found: {cpt_count}")
print(f"  Total rates extracted: {rates_found:,}")

df_rates = pd.read_sql("""
    SELECT cpt_code,
           COUNT(DISTINCT npi) as providers,
           AVG(negotiated_rate) as avg_rate,
           MIN(negotiated_rate) as min_rate,
           MAX(negotiated_rate) as max_rate
    FROM rates
    GROUP BY cpt_code
    ORDER BY cpt_code
""", conn)
print("\nRate summary by CPT code:")
print(df_rates.to_string())

conn.close()