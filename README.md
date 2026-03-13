# Healthcare Cost Engine

Normalizes government-mandated healthcare price transparency data to estimate 
visit costs and verify insurance coverage for SF-based primary care providers.

## POC Scope
- **Geography:** San Francisco County
- **Insurance:** Anthem Blue Cross PPO
- **Visit types:** Base office visit cost only — additional charges 
  (labs, procedures, vaccines) not included

### Provider Taxonomy (NUCC v25.1)

| Code | Specialty | Source |
|---|---|---|
| `207Q00000X` | Family Medicine | NUCC direct verification |
| `207QA0505X` | Family Medicine — Adult Medicine | NUCC direct verification |
| `207QG0300X` | Family Medicine — Geriatric Medicine | NUCC direct verification |
| `208D00000X` | General Practice | NUCC direct verification |
| `207R00000X` | Internal Medicine | NUCC direct verification |
| `207RG0300X` | Internal Medicine — Geriatric Medicine | NUCC direct verification |

**Source:** NUCC Health Care Provider Taxonomy Code Set v25.1  
https://taxonomy.nucc.org

**Out of scope for POC:** Med-Peds (no dedicated NUCC taxonomy code), 
OB/GYN as PCP, Pediatrics, Hospitalist, Integrative Medicine

### Visit CPT Codes

| Code | Type | Complexity |
|---|---|---|
| 99202 | New patient | Straightforward |
| 99203 | New patient | Low |
| 99204 | New patient | Moderate |
| 99205 | New patient | High |
| 99211 | Established patient | Minimal |
| 99212 | Established patient | Straightforward |
| 99213 | Established patient | Low |
| 99214 | Established patient | Moderate |
| 99215 | Established patient | High |
| G2211 | Add-on | Longitudinal care complexity |

**Source:** AMA CPT E/M guidelines, CMS CY2026 Physician Fee Schedule  
**Note:** Costs reflect negotiated rate for base visit only. Labs, imaging, 
vaccines, and procedures billed separately.

## Data Sources

| Source | Publisher | Used For | Status |
|---|---|---|---|
| NPPES | CMS | Primary provider list + NPI | Active |
| MBC Physician Database | Medical Board of CA | License status verification | Active |
| Anthem TiC MRF | Anthem Blue Cross | Negotiated rates — Anthem PPO | POC |
| Blue Shield TiC MRF | Blue Shield of CA | Negotiated rates — Blue Shield HMO + PPO | Planned |
| Kaiser TiC MRF | Kaiser Permanente | Negotiated rates — Kaiser HMO | Planned |
| Hospital Price Transparency MRFs | CMS | Facility-level pricing | Planned |
| DHCS Medi-Cal Provider File | CA Dept of Health Care Services | Medi-Cal network + fee schedule | Planned |

## Pipeline
```
NPPES → SF active PCPs by taxonomy code + NPI
      ↓
MBC → verify license is active
      ↓
Anthem TiC MRF → negotiated rate by NPI + CPT code
      ↓
Cost estimator UI (Streamlit)
```

## Status

| Step | Description | Status |
|---|---|---|
| 1 | SF PCP extraction from NPPES | In progress |
| 2 | License verification via MBC | Not started |
| 3 | Anthem TiC MRF rate ingestion | Not started |
| 4 | Streamlit UI | Not started |

## Known Issues
- NPPES taxonomy is self-selected by provider — some PCPs may use 
  non-standard taxonomy codes
- MBC survey is voluntary — some active physicians have no practice 
  location or specialty data on file
- TiC MRF negotiated rates reflect insurer-provider contracts, not patient 
  OOP costs (which depend on deductible + coinsurance)
- Cost estimate covers base visit only — labs, imaging, vaccines billed 
  separately

## Stack
Python, pandas, pyodbc, ijson, SQLite, Streamlit
