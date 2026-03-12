import pyodbc
import pandas as pd

db_path = r"C:\Users\hinag\healthcare-cost-engine\MBCPhysicianAndSurgeonInformation_3.10.2026\MBCPhysicianAndSurgeonInformation-PUBLIC.accdb"

conn_str = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={db_path};"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

query = """
SELECT 
    l.LicenseID,
    l.FirstName,
    l.LastName,
    l.LicenseNumber,
    s.PatientCarePrimaryZipCode,
    r.SurveyResponseCode,
    ref.Description AS Specialty
FROM ((License l
INNER JOIN LicenseSurveyPracticeLocationResponse s
    ON l.LicenseID = s.LicenseID)
INNER JOIN LicenseSurveyResponseCodes r
    ON l.LicenseID = r.LicenseID)
INNER JOIN REF_SurveyResponseCode ref
    ON r.SurveyResponseCode = ref.SurveyResponseCode
WHERE s.PatientCarePrimaryCountyCode = '38'
AND l.PrimaryStatusCode = '20'
AND r.SurveyResponseCode IN ('04aFAMMED1','04aINTMED1','04aGENPRAC1','04aGERIMED1')
"""

cursor.execute(query)
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
df = pd.DataFrame.from_records(rows, columns=columns)
conn.close()

print(f"SF primary care physicians found: {len(df)}")
print(df.head(10).to_string())

df.to_csv("data/sf_primary_care_providers.csv", index=False)
print("\nSaved to data/sf_primary_care_providers.csv")