import pyodbc
import pandas as pd

db_path = r"C:\Users\hinag\healthcare-cost-engine\MBCPhysicianAndSurgeonInformation_3.10.2026\MBCPhysicianAndSurgeonInformation-PUBLIC.accdb"

conn_str = (
    r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
    rf"DBQ={db_path};"
)

conn = pyodbc.connect(conn_str)

query = """
SELECT 
    l.LicenseID,
    l.LicenseNumber,
    l.FirstName,
    l.LastName,
    l.PrimaryStatusCode,
    s.PatientCarePrimaryZipCode,
    s.PatientCarePrimaryCountyCode
FROM License l
LEFT JOIN LicenseSurveyPracticeLocationResponse s
    ON l.LicenseID = s.LicenseID
WHERE s.PatientCarePrimaryCountyCode = '38'
AND l.PrimaryStatusCode = '20'
"""

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
cursor.execute(query)
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
df = pd.DataFrame.from_records(rows, columns=columns)
conn.close()

print(f"Active SF physicians: {len(df)}")
print(df.head(10).to_string())