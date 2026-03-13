import pandas as pd

INPUT_FILE = r"C:\Users\hinag\healthcare-cost-engine\data\sf_providers_nppes.csv"
OUTPUT_FILE = r"C:\Users\hinag\healthcare-cost-engine\data\sf_providers_clean.csv"

SF_ZIPS = {
    "94102", "94103", "94104", "94105", "94107", "94108", "94109", "94110",
    "94111", "94112", "94114", "94115", "94116", "94117", "94118", "94121",
    "94122", "94123", "94124", "94127", "94129", "94130", "94131", "94132",
    "94133", "94134", "94158", "94188"
}

VALID_TAXONOMY_CODES = {
    "207Q00000X",   # Family Medicine
    "207QA0505X",   # Family Medicine, Adult Medicine
    "207QG0300X",   # Family Medicine, Geriatric Medicine
    "208D00000X",   # General Practice
    "207R00000X",   # Internal Medicine
    "207RG0300X",   # Internal Medicine, Geriatric Medicine
}

df = pd.read_csv(INPUT_FILE, dtype=str)

print(f"Before cleaning: {len(df)}")

# Filter 1: must be in SF zip code
df = df[df["zip"].isin(SF_ZIPS)]
print(f"After SF zip filter: {len(df)}")

# Filter 2: must have a valid primary care taxonomy code
df = df[df["taxonomy_code"].isin(VALID_TAXONOMY_CODES)]
print(f"After taxonomy filter: {len(df)}")

# Filter 3: must be in CA
df = df[df["state"] == "CA"]
print(f"After state filter: {len(df)}")

print(f"\nSpecialty breakdown:")
print(df["taxonomy_desc"].value_counts().to_string())

print(f"\nSample:")
print(df.head(10).to_string())

df.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved to {OUTPUT_FILE}")