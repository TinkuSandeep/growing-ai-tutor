python3 - <<'PY'  
import os  
import pyodbc  
  
driver = os.environ["DB_DRIVER"]  
host = os.environ["DB_HOST"]  
port = os.environ["DB_PORT"]  
database = os.environ["DB_NAME"]  
user = os.environ["DB_USER"]  
pwd = os.environ["DB_PASSWORD"]  
  
conn_str = (  
    f"DRIVER={{{driver}}};"  
    f"SERVER={{{host},{port}}};"  
    f"DATABASE={{{database}}};"  
    f"UID={{{user}}};"  
    f"PWD={{{pwd}}};"  
    "Encrypt=yes;"  
    "TrustServerCertificate=yes;"  
)  
  
print(f"Testing DB connection to {host}:{port}/{database}")  
  
try:  
    conn = pyodbc.connect(conn_str, timeout=15)  
    print("SUCCESS: Database connection established")  
  
    cursor = conn.cursor()  
    cursor.execute("SELECT @@SERVERNAME, DB_NAME()")  
    print("Server/Database:", cursor.fetchone())  
  
    cursor.close()  
    conn.close()  
  
except Exception as e:  
    print("FAILED:", type(e).__name__)  
    print(e)  
PY  
