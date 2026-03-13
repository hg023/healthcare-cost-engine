# Healthcare Cost Engine

Normalizes government-mandated healthcare price transparency data to estimate 
visit costs and verify insurance coverage for SF-based primary care providers.

## POC Scope
- **Geography:** San Francisco County
- **Providers:** Primary care physicians (Family Medicine, Internal Medicine, 
  General Practice, Geriatric Medicine)
- **Insurance:** Anthem Blue Cross PPO
- **Visit types:** Base office visit cost only — additional charges 
  (labs, procedures, vaccines) not included

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
| MBC Physician Database | Medical Board of CA | SF provider list + license status | Active |
| NPPES | CMS | NPI resolution for rate lookup | In progress |
| Anthem TiC MRF | Anthem Blue Cross | Negotiated rates — Anthem PPO | POC |
| Blue Shield TiC MRF | Blue Shield of CA | Negotiated rates — Blue Shield HMO + PPO | Planned |
| Kaiser TiC MRF | Kaiser Permanente | Negotiated rates — Kaiser HMO | Planned |
| Hospital Price Transparency MRFs | CMS | Facility-level pricing | Planned |
| DHCS Medi-Cal Provider File | CA Dept of Health Care Services | Medi-Cal network + fee schedule | Planned |

## Pipeline
```
MBC database → SF active PCPs (964)
      ↓
NPPES fuzzy match → NPI per provider
      ↓
Anthem TiC MRF → negotiated rate by NPI + CPT code
      ↓
Cost estimator UI (Streamlit)
```

## Status

| Step | Description | Status |
|---|---|---|
| 1 | SF PCP extraction from MBC | Done |
| 2 | NPI matching via NPPES | In progress |
| 3 | Anthem TiC MRF rate ingestion | Not started |
| 4 | Streamlit UI | Not started |

## Known Issues
- MBC survey is voluntary — some active physicians have no practice location 
  or specialty data on file
- NPI fuzzy match on name + zip will miss providers with address discrepancies
- TiC MRF negotiated rates reflect insurer-provider contracts, not patient OOP 
  costs (which depend on deductible + coinsurance)
- Cost estimate covers base visit only — labs, imaging, vaccines billed separately

## Stack
Python, pandas, pyodbc, ijson, SQLite, Streamlit
