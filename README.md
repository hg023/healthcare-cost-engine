# Healthcare Cost Engine

Healthcare Cost Engine is a price transparency tool that helps people predict and understand the cost of a healthcare visit before they book an appointment.

The engine utilizes publicly available negotiated rates for in-network providers and services, as mandated by the Transparency in Coverage Rule. It extracts, normalizes, and surfaces data from machine-readable files (MRFs) so people can review a list of providers and compare costs upfront in order to make informed decisions before scheduling a visit.

### POC Scope

| Dimension | Scope |
|---|---|
| Geography | San Francisco |
| Insurance | Anthem Blue Cross PPO |
| Provider type | Primary care (Family Medicine, Internal Medicine, General Practice) |
| Visit scenarios | TBD — to be defined after MRF profiling and rate extraction |
| Output | Search results (eligible in-network doctors), estimated cost per doctor per location, cost breakdown by billing code with confidence indicator |

### Data Sources

#### #1
| | |
|---|---|
| **Source** | National Provider Identifier Registry (NPPES) |
| **Description** | Registry of licensed healthcare providers in the US |
| **Publisher** | Centers for Medicare & Medicaid Services (CMS) |
| **Format** | CSV |
| **Key Attributes** | NPI, Provider Name, Specialty, Credential, Address, Phone |
| **Raw Data Fields** | npi, provider_first_name, provider_last_name, provider_credential_text, provider_first_line_business_practice_location_address, provider_business_practice_location_address_city_name, provider_business_practice_location_address_postal_code, provider_business_practice_location_address_telephone_number, healthcare_provider_taxonomy_code |
| **Used For** | Provider list (1,337 SF primary care doctors), practice locations, taxonomy codes (zombie rate filtering) |
| **Status** | Downloaded and processed. `sf_providers_clean.csv` |

#### #2
| | |
|---|---|
| **Source** | Insurance Carrier Machine-Readable File (MRF) |
| **Description** | Negotiated rates for in-network providers and services, as mandated by the Transparency in Coverage (TiC) Rule |
| **Publisher** | Insurance Carrier (Anthem Blue Cross for POC) |
| **Format** | Machine-Readable File (MRF) — JSON, gzip compressed |
| **Key Attributes** | Provider group, Tax ID, Network, Billing code, Negotiated rate, Rate type, Billing class |
| **Raw Data Fields** | provider_group_id, tin.type, tin.value, network_name, billing_code, billing_code_type, negotiated_rate, negotiated_type, billing_class, expiration_date, service_code, billing_code_modifier |
| **Used For** | Negotiated rates between Anthem and in-network providers |
| **Known Issues** | Zombie rates (40–80% of data), missing providers, anomalous rate ordering, schema deviations from CMS spec |
| **Status** | Downloaded. `CA_AHPNMED0000_01_04.json.gz`, 11.91 GB. Partial extraction exists (13,167 rates) — needs to be redone after profiling. |

#### #3
| | |
|---|---|
| **Source** | Medical Board of California (MBC) |
| **Description** | License verification for physicians and surgeons in California |
| **Publisher** | Medical Board of California |
| **Format** | Microsoft Access DB (refreshed weekly) |
| **Key Attributes** | Physician name, License number, License status, Disciplinary actions |
| **Raw Data Fields** | TBD from file inspection |
| **Used For** | Validating that every doctor in search results has an active license |
| **Known Issues** | MBC does not collect NPI — matching to NPPES requires name matching |
| **Status** | Available locally. Not yet integrated. |

#### #4
| | |
|---|---|
| **Source** | CMS Physician Fee Schedule / RVU File |
| **Description** | Medicare payment amounts and relative value units per CPT code, nationally and by locality |
| **Publisher** | Centers for Medicare & Medicaid Services (CMS) |
| **Format** | CSV (ZIP download, ~4 MB) |
| **Key Attributes** | HCPCS code, Description, Work RVU, PE RVU (facility + non-facility), MP RVU, Totals, Conversion factor |
| **Raw Data Fields** | hcpcs, mod, description, status_code, work_rvu, non_fac_pe_rvu, fac_pe_rvu, mp_rvu, non_facility_total, facility_total, conv_factor |
| **Used For** | Sanity check baseline for MRF rates. Expected rate ordering between codes. Percentage rate conversion. |
| **Status** | Not yet downloaded. Free from CMS. |

#### #5
| | |
|---|---|
| **Source** | Hospital Machine-Readable Files |
| **Description** | Hospital-published price transparency files including facility fees |
| **Publisher** | Individual hospitals (UCSF, Sutter/CPMC, Dignity Health) |
| **Format** | Varies — CSV or JSON per CMS v2.0 schema |
| **Key Attributes** | Hospital name, Billing code, Payer name, Negotiated rate, Gross charge |
| **Raw Data Fields** | TBD — varies by hospital |
| **Used For** | Facility fees at hospital-owned outpatient locations |
| **Status** | Not yet investigated. |

#### #6
| | |
|---|---|
| **Source** | CPT Code Descriptions |
| **Description** | Standardized codes defining the type and complexity of a healthcare service |
| **Publisher** | American Medical Association (AMA) / CMS (short descriptions) |
| **Format** | CSV |
| **Key Attributes** | Billing code, Short description, Long description |
| **Raw Data Fields** | procedure_code, short_description, long_description |
| **Used For** | Patient-facing labels — translating codes into plain language |
| **Status** | Available within CMS PFS download. |

### Database Design

Design is pending MRF profiling results. The database needs to represent five components:

**Component 1: Doctors**

| Attribute | Description | Source |
|---|---|---|
| Identity | NPI, name, credentials | NPPES |
| Specialty | Taxonomy code, specialty description | NPPES |
| License | License number, status, verification date | MBC |
| Practice locations | All addresses where they see patients | NPPES |
| Facility affiliation | Per location: private practice or hospital-owned | NPPES + Hospital MRFs |

**Component 2: Rates**

| Attribute | Description | Source |
|---|---|---|
| Provider-to-rate link | How the MRF connects NPIs to rates (groups, TIN) | Carrier MRF |
| Rate details | Billing code, dollar amount, rate type, billing class, network, expiration | Carrier MRF |
| Filtering | All rates stored raw; zombies/anomalies flagged, not deleted | — |

*Exact structure depends on MRF profiling results.*

**Component 3: Procedures**

| Attribute | Description | Source |
|---|---|---|
| Code reference | CPT/HCPCS code, plain-language description | CMS / AMA |
| Visit scenarios | Which codes make up a visit type, with probability weights | CMS claims data |

**Component 4: Cost Validation**

| Attribute | Description | Source |
|---|---|---|
| Medicare rates | Payment amount per code, national + SF locality | CMS PFS |
| RVU values | Expected relationships between codes | CMS RVU file |
| Conversion factor | For converting percentage-type rates to dollars | CMS RVU file |

**Component 5: Facilities**

| Attribute | Description | Source |
|---|---|---|
| Facility identity | NPI, name, type | NPPES |
| Ownership | Health system affiliation | Manual + NPPES taxonomy |
| Facility fees | Institutional rates at hospital-owned locations | Hospital MRFs + Carrier MRF |

*Depends on investigation of hospital MRF files.*

### Extraction Pipeline

| Step | Input | Action | Output | Dependencies | Status |
|---|---|---|---|---|---|
| 1. Providers + Locations | NPPES CSV | Filter to SF zips + primary care taxonomies. Extract all practice locations per NPI. | Providers, Locations | None | Done. 1,337 providers. Locations need breakout. |
| 2. License Verification | MBC Access DB | Match providers by name to MBC records. Flag license status. | License status per provider | Step 1 | Not started |
| 3. MRF Profiling | Anthem MRF (11.91 GB) | Run exhaustive profiler. Discover all field paths, types, value sets, cross-field patterns. | Field catalog, enum values, numeric stats, anomaly report | None | Script ready. Needs re-run. |
| 4. MRF Rate Extraction | MRF + profiling results | Stream MRF, extract all rates for POC CPT codes. Store all rate types and billing classes. Build provider group and junction tables. | Rates, Provider groups, Junction table | Step 3 | Blocked |
| 5. Zombie Rate Filtering | Extracted rates + taxonomy codes | Check if provider taxonomy can realistically bill each CPT code. Flag non-billable rates. | `is_suspect` flag per rate | Steps 1, 4 | Blocked |
| 6. Medicare Reference Data | CMS PFS/RVU download | Download, filter to POC CPT codes + SF locality. Load into reference table. | CPT codes with descriptions, RVUs, Medicare rates | None | Not started |
| 7. Facility Identification | NPPES + Hospital MRFs | Per provider location, determine if hospital-owned. Tag with ownership type. | Facility flags on locations | Step 1 | Not started |
| 8. Cost Validation | Extracted rates + Medicare rates | Compare MRF rates against Medicare baseline. Flag outliers. Check code ordering. | Confidence flags, suspect flags | Steps 4, 6 | Blocked |

**Can start now:** Steps 1 (location breakout), 2, 3 (re-run), 6

**Blocked by MRF profiling:** Steps 4, 5, 8

### Out of Scope for POC

| Excluded | Reason |
|---|---|
| Patient out-of-pocket (deductible, copay, coinsurance) | Requires patient's specific plan design |
| Prescription costs | Not in MRF data |
| Out-of-network providers | Different data source and pricing model |
| Insurers other than Anthem | POC is single-carrier |
| Geographies outside San Francisco | POC is single-market |
| Specialties beyond primary care | POC is single-specialty |
| Preventive visits / annual physicals | Different CPT code set (99381–99397). First expansion. |
| Telehealth pricing | Different modifier and rate structure |
| User accounts / login | Not needed for POC |
| Feedback loop (user-reported actual bills) | Post-launch feature |
| Real-time MRF updates | POC uses a single point-in-time extract |

### Findings from Data So Far

#### MRF Structure

| Finding | Detail |
|---|---|
| File size | 11.91 GB compressed (`CA_AHPNMED0000_01_04.json.gz`) |
| Provider references | 5.4M provider_reference entries scanned |
| Billing codes | 39,323 in in_network section (first 1,000 entries) |
| Provider groups per reference | Average 16.8 (first 1,000 entries) |
| Negotiated rates per billing code | Average 192 (first 1,000 entries) |
| Billing code types found | CPT, HCPCS, ICD, MS-DRG, APC, RC, CSTM-ALL |
| Rate types found | fee schedule, per diem, percentage, negotiated, derived |
| Billing classes found | professional, institutional |
| provider_reference type | Integer (not string — critical for matching) |
| service_code and billing_code_modifier | Always lists (JSON arrays) |

⚠️ Structural profiling based on first 1,000 entries only. Full-file profiling not yet complete.

#### Provider Coverage

| Metric | Count |
|---|---|
| SF primary care providers extracted from NPPES | 1,337 |
| Providers found in Anthem MRF | 566 (42%) |
| Providers absent from MRF | 771 (58%) |
| Sample provider (Justin Ren) group memberships | 9,152 groups |

#### Rate Extraction (Preliminary — needs redo)

| Metric | Value |
|---|---|
| Matched provider groups | 282,827 |
| Rate records extracted | 13,167 |
| CPT codes targeted | 10 (99202–99215, G2211) |
| Rate types included | fee schedule, negotiated only (percentage, per diem, derived excluded — this was an error) |
| Billing classes included | professional, both only (institutional excluded — this was an error) |

#### Known Data Quality Issues

| Issue | Detail | Impact |
|---|---|---|
| 99204 avg > 99205 avg | $614 vs $388 — higher complexity code should cost more | Possible mix of rate types being compared as dollar amounts |
| Ghost/zombie rates | Industry estimates: 40–80% of MRF rates are for services the provider would never bill | Taxonomy filtering required — match provider specialty to CPT code |
| Missing providers | 58% of NPPES providers absent from MRF | MRF may not cover all Anthem networks; some providers may contract under different TINs |
| Provider group explosion | Single provider can belong to thousands of groups | Junction table with unique constraint required to prevent row explosion |
| Schema non-compliance | MRF files deviate from CMS spec — additional fields/values beyond spec | Full-file profiling needed before finalizing database schema |
| Rate types excluded in initial extraction | Percentage, per diem, derived rates were filtered out | Re-extraction must include all rate types |
| Billing class excluded in initial extraction | Institutional class filtered out | Facility fees cannot be calculated without institutional rates |

### Key Blockers

| Blocker | Impact | Next Step |
|---|---|---|
| MRF profiling not complete | Cannot finalize database schema or extraction pipeline | Re-run profiler on second machine (32 GB RAM) |
| Hospital MRFs not investigated | Cannot calculate facility fees | Locate and assess UCSF, Sutter, Dignity published files |
| MBC integration not started | Cannot verify provider licenses | Inspect Access DB, build name-matching pipeline |
| CMS PFS/RVU not downloaded | Cannot validate MRF rates against Medicare baseline | Download from CMS — small file, straightforward |
