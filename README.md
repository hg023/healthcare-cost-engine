# Healthcare Cost Engine

> Transforming CMS-mandated Transparency in Coverage (TiC) machine-readable files into accurate, upfront cost predictions for patients navigating primary care in San Francisco.

**Status:** Pilot — rate extraction complete, UI in development  
**Author:** Hina Ghazi · [github.com/hg023](https://github.com/hg023)  
**Stack:** Python · ijson · SQLite · Streamlit · NPPES API · Anthem TiC MRF (CMS schema v2.0)

---

## Problem

The TiC Rule (45 CFR Parts 147, 150, 158 — effective July 2022) requires insurers to publish monthly machine-readable files containing every negotiated rate for every in-network provider. The data is public. The access is not.

MRF files are multi-gigabyte JSON structures requiring specialized infrastructure to process. The Anthem CA in-network file alone is **11.91 GB compressed**. No patient can realistically use this data directly.

The result:
- Patients cannot compare provider costs before choosing one
- When the EOB arrives, CPT codes appear with brief descriptions that rarely explain why a code was used, whether it was expected, or how it maps to what happened in the visit
- The gap between an estimated cost and the final bill is a direct consequence of inaccessible, poorly explained data

**This project closes that gap** — extracting, normalizing, and surfacing TiC data so patients can find in-network providers, understand the billing codes that drive their visit cost at the level of detail that appears on their actual bill, and anticipate their final EOB before the appointment.

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

## User Flow

### Step 1 — Insurance and employer
User selects Anthem PPO and their employer. Employer determines which negotiated rates apply — the same provider can have different rates across different employer plans. Pilot uses a curated list of pre-processed SF employers. Users whose employer is not listed see the Prudent Buyer PPO range with a clear caveat.

### Step 2 — Visit type
User selects new patient or existing patient. Maps to CPT code family behind the scenes — no codes shown at this step.

### Step 3 — Location
User enters SF zip code or neighborhood. Filters to providers with a practice location in or near that area.

### Step 4 — Provider results
Ranked list of matching in-network providers showing name, specialty, address, phone, and estimated cost range for their visit type. Sortable by cost and distance.

### Step 5 — Billing detail
Clicking a provider shows the full CPT code breakdown — the same structure that will appear on their EOB after the visit:

| What appears on your EOB | Plain English | Estimated Anthem Rate |
|---|---|---|
| 99203 | New patient visit — low complexity | $135 |
| G2211 | Ongoing care relationship add-on | +$21 |
| **Total estimated** | | **$156** |

Each code includes: plain-language description, estimated negotiated rate, whether it is likely for their visit type, and a clear note that patient responsibility depends on their specific plan's deductible, copay, and coinsurance.

---

## Data Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                          │
├─────────────────┬──────────────────┬────────────────────────┤
│   NPPES API     │   MBC Access DB  │   Anthem TiC MRF       │
│   CMS · weekly  │  CA DCA · weekly │  Anthem · monthly      │
└────────┬────────┴────────┬─────────┴──────────┬─────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
  fetch_sf_providers_   MBC license        extract_anthem_
  nppes.py              verification       rates.py
  ─────────────────     (skipped:          ──────────────
  Filter by:            pilot)             Pass 1: stream
  · SF zip codes                           provider_references
  · NUCC taxonomy                          → NPI lookup
  · Status = Active                        
                                           Pass 2: stream
                                           in_network
                                           → match CPT codes
                                           → extract rates
         │                                      │
         └──────────────────┬───────────────────┘
                            ▼
              ┌─────────────────────────┐
              │      SQLite Database    │
              │                         │
              │  providers table        │
              │  rates table            │
              │  13,167 rate records    │
              │  566 SF providers       │
              │  10 CPT codes           │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │     Streamlit UI        │
              │   (in development)      │
              └─────────────────────────┘
```

---

## MRF Architecture

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

## Data Sources

| Source | Publisher | Mandate | Used For | Refresh |
|---|---|---|---|---|
| NPPES National Provider Registry | CMS | HIPAA — every billing provider must have NPI | SF provider list — NPI, name, address, specialty | Weekly |
| Medical Board of California | CA Dept of Consumer Affairs | CA Business & Professions Code | License status verification | Weekly |
| Anthem TiC MRF — In-Network Rates | Anthem Blue Cross CA | 45 CFR Parts 147, 150, 158 | Negotiated rates by NPI + CPT code | Monthly |
| NUCC Taxonomy Code Set v25.1 | NUCC / CMS | HIPAA standard code set | Provider specialty classification | Biannual |
| CMS E/M Services Guide | CMS / AMA | Medicare PFS Final Rule | CPT code definitions + billing class | Annual |

---

## Data Architecture

### Pilot (Local)

| Component | Technology |
|---|---|
| Provider extraction | Python 3.14 · pandas · requests — NPPES REST API |
| License verification | Python · pyodbc — MBC Access DB (.accdb) — skipped in pilot |
| MRF ingestion | Python · ijson streaming parser · gzip — local file |
| Rate storage | SQLite |
| UI | Streamlit — in development |

### Phase 1 (Hosted Beta)

| Component | Technology |
|---|---|
| Rate database | Supabase (PostgreSQL) |
| UI hosting | Streamlit Community Cloud |
| MRF ingestion pipeline | Python · GitHub Actions — monthly schedule |
| Employer file access | Playwright — signed CloudFront URL automation |
| Monitoring | Datadog |

### Data Refresh Cadence

| Source | Frequency |
|---|---|
| Anthem TiC MRF | Monthly — published 1st of each month |
| NPPES provider registry | Weekly |
| MBC license database | Weekly — Monday refresh |

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

## Pipeline Status

| Step | Description | Status |
|---|---|---|
| 1 | SF PCP extraction from NPPES | ✅ Done — 1,337 providers |
| 2 | License verification via MBC | ⏭ Skipped — pilot |
| 3 | Anthem MRF download | ✅ Done — 11.91 GB |
| 4 | Pass 1 — provider group lookup | ✅ Done — 5.4M groups, 566 SF providers found |
| 5 | Pass 2 — rate extraction | ✅ Done — 13,167 rates across 10 CPT codes |
| 6 | Rate validation vs Medicare benchmark | 🔄 In progress |
| 7 | Streamlit UI | 🔄 In development |

---

## Project Structure

```
healthcare-cost-engine/
├── fetch_sf_providers_nppes.py   # NPPES provider extraction
├── clean_providers.py            # Filter to valid SF zips + taxonomy
├── extract_anthem_rates.py       # Two-pass MRF rate extraction
├── download_mrf.py               # MRF file download with resume
├── find_ca_mrf.py                # Anthem index scan — CA URL extraction
├── peek_mrf.py / peek_mrf2.py   # MRF file inspection utilities
├── check_mrf.py / check_mrf_sizes.py  # MRF access + size checks
├── explore_mbc.py                # MBC Access DB exploration
├── explore_survey_codes.py       # MBC survey code reference
├── lookup_doctor.py              # Single provider lookup utility
├── data/                         # Output files (gitignored)
│   ├── sf_providers_clean.csv    # 1,337 SF primary care providers
│   ├── anthem_ca_mrf_urls.txt    # 17,176 CA Anthem plan entries
│   ├── group_lookup.pkl          # Provider group → NPI lookup
│   └── anthem_rates.db           # SQLite — 13,167 rate records
└── README.md
```

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

*Healthcare Cost Engine · March 2026 · Hina Ghazi*  
*Data sources: CMS NPPES · Medical Board of California · Anthem Blue Cross CA TiC MRF*  
*Regulatory basis: 45 CFR Parts 147, 150, 158 (Transparency in Coverage Rule)*
