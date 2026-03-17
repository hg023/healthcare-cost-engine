# Healthcare Cost Engine

Healthcare Cost Engine is a price transparency tool that helps people predict and understand the cost of a healthcare visit before they book an appointment.

The engine utilizes publicly available negotiated rates for in-network providers and services, as mandated by the Transparency in Coverage Rule. It extracts, normalizes, and surfaces data from machine-readable files (MRFs) so people can review a list of providers and compare costs upfront in order to make informed decisions before scheduling a visit.

---

## How it works
| # | Source | Description | Publisher | Format | Key Attributes | Raw Data Fields |
|---|--------|-------------|-----------|--------|----------------|-----------------|
| 1 | National Provider Identifier Registry (NPPES) | Registry of licensed healthcare providers in the US | Centers for Medicare & Medicaid Services (CMS) | CSV | NPI, Provider Name, Specialty, Credential, Address, Phone | npi, provider_first_name, provider_last_name, provider_credential_text, provider_first_line_business_practice_location_address, provider_business_practice_location_address_city_name, provider_business_practice_location_address_postal_code, provider_business_practice_location_address_telephone_number, healthcare_provider_taxonomy_code |
| 2 | Insurance Carrier | Negotiated rates for in-network providers and services, as mandated by the Transparency in Coverage (TiC) Rule | Insurance Carrier | Machine-Readable File (MRF) — JSON | Provider group, Tax ID, Network, Billing code, Negotiated rate, Rate type, Billing class | provider_group_id, tin.type, tin.value, network_name, billing_code, billing_code_type, negotiated_rate, negotiated_type, billing_class, expiration_date, service_code, billing_code_modifier |
| 3 | Current Procedural Terminology (CPT) Codes | Standardized codes defining the type and complexity of a healthcare service | American Medical Association (AMA) / Centers for Medicare & Medicaid Services (CMS) | CSV | Billing code, Description, Complexity level | procedure_code, short_description, long_description, complexity_level |



------------------------------



---

## Pilot Scope

| Dimension | Pilot |
|---|---|
| Geography | San Francisco County (zip codes 94102–94188) |
| Insurance | Anthem Blue Cross PPO |
| Provider type | Primary care — see taxonomy table below |
| Visit types | New patient (CPT 99202–99205), established patient (CPT 99211–99215), add-on G2211 |
| Employer scope | Select SF employers — TBD pending MRF file access verification |
| Rate source | Anthem CA MRF — `CA_AHPNMED0000`, March 2026, CMS TiC schema v2.0 |
| Cost shown | Negotiated rate — what Anthem has contracted to pay the provider. Patient OOP cost not modeled in pilot. |

### Provider Taxonomy (NUCC v25.1 — verified at taxonomy.nucc.org)

| Code | Specialty |
|---|---|
| `207Q00000X` | Family Medicine |
| `207QA0505X` | Family Medicine — Adult Medicine |
| `207QG0300X` | Family Medicine — Geriatric Medicine |
| `208D00000X` | General Practice |
| `207R00000X` | Internal Medicine |
| `207RG0300X` | Internal Medicine — Geriatric Medicine |

### Visit CPT Codes (CMS E/M Guidelines + AMA CPT + CMS CY2026 Physician Fee Schedule)

| Code | Type | Complexity | Pilot Avg Rate | Min | Max |
|---|---|---|---|---|---|
| 99202 | New patient | Straightforward | $88 | $53 | $273 |
| 99203 | New patient | Low | $135 | $72 | $465 |
| 99204 | New patient | Moderate | $614 | $138 | $812 |
| 99205 | New patient | High | $388 | $142 | $665 |
| 99211 | Established patient | Minimal | $17 | $11 | $92 |
| 99212 | Established patient | Straightforward | $52 | $29 | $165 |
| 99213 | Established patient | Low | $133 | $53 | $321 |
| 99214 | Established patient | Moderate | $523 | $71 | $546 |
| 99215 | Established patient | High | $642 | $71 | $725 |
| G2211 | Add-on | Longitudinal care complexity | $21 | $13 | $95 |

> ⚠️ Rate validation against CMS Medicare Physician Fee Schedule benchmark in progress. 99204 avg ($614) exceeds 99205 avg ($388) — higher complexity code should have higher rate. Known MRF data quality issue under investigation.

> Note: Cost estimate covers base office visit only. Labs, imaging, and vaccines are billed separately — see Phase 1 scope below.

---

## Scope — Exclusions and Phased Expansion

### Pilot Exclusions — Not in Pilot, Addressed in Phases

| Item | Reason | Phase |
|---|---|---|
| Labs, imaging, vaccines | Billed separately from office visit E/M code — require separate CPT families and rate extraction | Phase 1 |
| Good Faith Estimate generation | Regulatory product under No Surprises Act — requires rate accuracy validation before generating formal estimates | Phase 2 |
| Patient OOP calculation | Requires deductible, copay, coinsurance — not available in TiC MRF | Phase 2 |
| Blue Shield CA | Separate insurer MRF — same extraction approach | Phase 1 |
| Kaiser Permanente | Closed staff-model HMO — different data source and network structure | Phase 2 |
| Specialist visits | Separate CPT code families and network participation logic | Phase 2 |
| Medi-Cal | DHCS data source, different rate structure, separate regulatory framework | Phase 3 |
| Medicare | CMS fee schedule — not a TiC MRF product | Phase 3 |
| Facility fees | Institutional billing class — hospital outpatient, not professional | Phase 2 |
| Employer-specific rates | Anthem employer files on BCBS CDN require CloudFront authentication — not accessible without browser automation | Phase 1 |

### Phased Expansion

| Phase | Scope |
|---|---|
| **Pilot** | Anthem PPO · SF County · Primary care · Select employers · Base office visit rates |
| **Phase 1** | Hosted beta (Streamlit + Supabase) · Employer-specific rates via browser automation · Labs, imaging, vaccines · Blue Shield CA · All SF employer coverage |
| **Phase 2** | All California counties · Specialist visits · Facility fees · Patient OOP calculator · Kaiser · Good Faith Estimate generation · Mobile UI |
| **Phase 3** | Medi-Cal FFS · Covered California individual market · All provider types — urgent care, mental health, dental · Medicare Advantage |
| **Beyond** | Nationwide · All major commercial insurers · Public API · B2B HR/benefits portal · HIPAA compliance program · SOC 2 Type II |

---



### CMS TiC Schema v2.0 — In-Network Rates File Structure

```
root
├── reporting_entity_name     "Anthem Blue Cross California"
├── version                   "2.0.0"
├── last_updated_on           "2026-03-01"
│
├── provider_references[]     ← Pass 1: build NPI lookup
│   ├── provider_group_id     integer (primary key)
│   ├── network_name[]        ["CA PPO PRUDENT BUYER", "CA PPO SELECT", ...]
│   └── provider_groups[]
│       ├── npi[]             [1234567890, 9876543210, ...]
│       └── tin { type, value }
│
└── in_network[]              ← Pass 2: extract rates
    ├── billing_code_type     "CPT"
    ├── billing_code          "99214"
    └── negotiated_rates[]
        ├── provider_references  [42, 107, ...]  → maps to provider_group_id
        └── negotiated_prices[]
            ├── negotiated_rate  185.00
            ├── negotiated_type  "negotiated" | "fee schedule" | "derived" | ...
            ├── billing_class    "professional" | "institutional" | "both"
            └── expiration_date  "9999-12-31"
```

> Source: [CMS Price Transparency Guide — in-network-rates schema](https://github.com/CMSgov/price-transparency-guide/tree/master/schemas/in-network-rates)

### Two-Pass Extraction

```
Pass 1 — provider_references section (5.4M groups scanned)
  For each provider group:
    If any NPI matches target SF provider list (1,337 NPIs):
      Store {group_id → [sf_npis], network_names}
  Result: 282,827 matched groups · 566 SF providers found in MRF

Pass 2 — in_network section
  For each billing code entry:
    If billing_code in target CPT codes (99202-99215, G2211):
      For each negotiated_rate:
        If provider_references contains a matched group_id:
          If negotiated_type in ("negotiated", "fee schedule"):
            If billing_class in ("professional", "both"):
              Extract rate → store to SQLite
  Result: 13,167 rate records extracted
```

### MRF Access

| File location | Access | Notes |
|---|---|---|
| `antm-pt-prod...s3.amazonaws.com/anthem/CA_*` | ✅ Public | No auth required. Combined CA network file used for pilot. |
| `anthembcca.mrf.bcbs.com/*` | ❌ 403 | CloudFront signed URL required. Employer-specific files. Phase 1 dependency via browser automation. |

---



---

## Compliance

### HIPAA
The pilot collects no Protected Health Information (PHI). No user accounts, no login, no session or query storage. All data displayed is publicly mandated government data. HIPAA does not apply to the pilot. Phase 1 features that would trigger HIPAA applicability — deductible status input, claims history, member ID lookup — require BAAs, PHI handling procedures, and breach notification protocols before implementation.

### Transparency in Coverage Rule (45 CFR Parts 147, 150, 158)
All rate data is sourced from publicly mandated TiC MRF files. CMS has confirmed third parties may use MRF data to build consumer-facing price transparency tools.

### No Surprises Act
This tool is a pre-shopping aid, not a Good Faith Estimate (GFE). Patients are directed to request a formal GFE from their chosen provider before scheduling. GFE generation is a Phase 2 feature — dependent on rate accuracy validation.

### SOC 2 Readiness

| Control | Implementation |
|---|---|
| No PII stored | Stateless search — no user data retained |
| Data provenance | Every rate display includes source file, publisher, publication date |
| Pipeline audit log | All MRF ingestion runs logged with source, timestamp, record counts, error rates |
| Secrets management | Credentials via environment variables — not hardcoded |
| Data retention | MRF source files retained 13 months for rate dispute audit trail |

---

## Known Limitations

### Provider Coverage
- NPPES practice location is self-reported — some providers have stale or incorrect SF addresses
- MBC survey is voluntary — some licensed physicians have no specialty or location data on file
- SF provider count (1,337 extracted, 566 with Anthem rates) is an undercount of the true SF PCP population

### Rate Accuracy
- **Employer rate variation** — the same provider has different negotiated rates across different Anthem employer plans. Pilot shows combined Prudent Buyer PPO network rates. Employer-specific accuracy is a Phase 1 dependency.
- **Ghost rates** — research estimates up to 60% of MRF-reported rates may be incorrectly attributed. Rates are being validated against CMS Medicare Physician Fee Schedule (Anthem PPO primary care rates should be 110–160% of Medicare). Anomalies identified: 99204 avg ($614) > 99205 avg ($388) — under investigation.
- **Rate lag** — MRF files updated monthly. Rates may be up to 30 days behind current contracted amounts.
- **OOP cost not modeled** — patient responsibility requires deductible, copay, and coinsurance — not in TiC MRF.

### MRF Access
- Anthem employer files on `anthembcca.mrf.bcbs.com` require CloudFront signed URL authentication — not accessible without browser automation
- Combined CA MRF (11.91 GB) requires full-file download and local processing — not suitable for real-time per-query processing
- Known industry access barrier — addressed by commercial vendors via dedicated infrastructure



---

## Tech Stack

| Layer | Technology |
|---|---|
| Data extraction | Python 3.14 · pandas · pyodbc · requests · ijson |
| Provider registry | NPPES REST API v2.1 |
| License verification | MBC Access DB (.accdb) via pyodbc |
| MRF ingestion | ijson streaming JSON parser · gzip decompression |
| Rate storage (pilot) | SQLite |
| Rate storage (Phase 1) | Supabase (PostgreSQL) |
| UI | Streamlit |
| Hosting (Phase 1) | Streamlit Community Cloud |
| Pipeline scheduling (Phase 1) | GitHub Actions |

---

