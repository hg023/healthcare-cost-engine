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
SELECT SurveyResponseCode, Description
FROM REF_SurveyResponseCode
ORDER BY SurveyResponseCode
"""

cursor.execute(query)
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
df = pd.DataFrame.from_records(rows, columns=columns)
conn.close()

print(f"Total survey response codes: {len(df)}")
print(df.to_string())