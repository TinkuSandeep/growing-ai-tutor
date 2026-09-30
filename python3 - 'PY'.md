python3 - <<'PY'  
import os  
import sys  
import pyodbc  
  
required = [  
    "DB_HOST",  
    "DB_PORT",  
    "DB_NAME",  
    "DB_USER",  
    "DB_PASSWORD",  
]  
  
missing = [name for name in required if not os.getenv(name)]  
if missing:  
    print("FAILED: Missing environment variables:", ", ".join(missing))  
    sys.exit(1)  
  
driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")  
host = os.environ["DB_HOST"]  
port = os.environ["DB_PORT"]  
database = os.environ["DB_NAME"]  
principal = os.environ["DB_USER"]  
credential = os.environ["DB_PASSWORD"]  
  
print("Testing SQL Server connection")  
print("Driver:", driver)  
print("Host:", host)  
print("Port:", port)  
print("Database:", database)  
print("Principal available:", bool(principal))  
print("Credential available:", bool(credential))  
  
connection_string = (  
    f"DRIVER={{{driver}}};"  
    f"SERVER={host},{port};"  
    f"DATABASE={database};"  
    f"UID={principal};"  
    f"PWD={credential};"  
    "Encrypt=yes;"  
    "TrustServerCertificate=no;"  
    "Connection Timeout=30;"  
)  
  
try:  
    with pyodbc.connect(connection_string) as connection:  
        cursor = connection.cursor()  
        cursor.execute(  
            "SELECT @@SERVERNAME, DB_NAME(), SUSER_SNAME(), GETDATE()"  
        )  
        server_name, database_name, login_name, server_time = cursor.fetchone()  
  
        print("SUCCESS: SQL Server connection established")  
        print("Connected server:", server_name)  
        print("Connected database:", database_name)  
        print("Login:", login_name)  
        print("Database time:", server_time)  
  
except Exception as error:  
    print("FAILED: SQL Server connection error")  
    print(type(error).__name__, str(error))  
    sys.exit(1)  
PY  
  
python3 - <<'PY'  
import os  
import sys  
from pathlib import Path  
  
import requests  
from requests.auth import HTTPBasicAuth  
  
required = [  
    "AUTOSYS_INSTANCE",  
    "AUTOSYS_API_USER",  
    "AUTOSYS_API_PASSWORD",  
]  
  
missing = [name for name in required if not os.getenv(name)]  
if missing:  
    print("FAILED: Missing environment variables:", ", ".join(missing))  
    sys.exit(1)  
  
instance = os.environ["AUTOSYS_INSTANCE"]  
principal = os.environ["AUTOSYS_API_USER"]  
credential = os.environ["AUTOSYS_API_PASSWORD"]  
  
template = os.getenv(  
    "AUTOSYS_BASE_URL_TEMPLATE",  
    "https://{instance}-autosyswebapi.wellsfargo.com/AEWS",  
)  
  
base_url = template.format(instance=instance)  
  
# Optional: provide the exact API path used in aews.py.  
test_path = os.getenv("AEWS_TEST_PATH", "")  
url = f"{base_url.rstrip('/')}/{test_path.lstrip('/')}" if test_path else base_url  
  
ca_path = Path("/mnt/certificates/wellsfargo-ca-bundle.pem")  
verify_value = str(ca_path) if ca_path.is_file() else True  
  
print("Testing AutoSys/AEWS connection")  
print("Instance:", instance)  
print("URL:", url)  
print("Principal available:", bool(principal))  
print("Credential available:", bool(credential))  
print("CA verification:", verify_value)  
  
try:  
    response = requests.get(  
        url,  
        auth=HTTPBasicAuth(principal, credential),  
        headers={  
            "Accept": "application/json",  
            "User-Agent": "1tcoo-batch-transformation-smoke-test",  
        },  
        timeout=30,  
        verify=verify_value,  
    )  
  
    print("HTTP status:", response.status_code)  
    print("Content type:", response.headers.get("Content-Type", "unknown"))  
  
    if 200 <= response.status_code < 300:  
        print("SUCCESS: AEWS endpoint and authentication are working")  
    elif response.status_code == 401:  
        print("FAILED: AEWS rejected the credentials")  
        sys.exit(1)  
    elif response.status_code == 403:  
        print("FAILED: Authentication succeeded but access is forbidden")  
        sys.exit(1)  
    elif response.status_code in (404, 405):  
        print("PARTIAL SUCCESS: AEWS server is reachable")  
        print("Set AEWS_TEST_PATH to the exact API route used by aews.py")  
    else:  
        print("AEWS returned:", response.text[:500])  
        sys.exit(1)  
  
except requests.exceptions.SSLError as error:  
    print("FAILED: AEWS TLS/certificate validation error")  
    print(str(error))  
    sys.exit(1)  
  
except requests.exceptions.ConnectionError as error:  
    print("FAILED: AEWS DNS/network/port connection error")  
    print(str(error))  
    sys.exit(1)  
  
except requests.exceptions.Timeout:  
    print("FAILED: AEWS request timed out")  
    sys.exit(1)  
  
except Exception as error:  
    print("FAILED:", type(error).__name__, str(error))  
    sys.exit(1)  
PY  
  
python3 - <<'PY'  
import os  
  
names = [  
    "DB_DRIVER",  
    "DB_HOST",  
    "DB_PORT",  
    "DB_NAME",  
    "DB_USER",  
    "DB_PASSWORD",  
    "AUTOSYS_API_USER",  
    "AUTOSYS_API_PASSWORD",  
]  
  
for name in names:  
    value = os.getenv(name)  
    print(f"{name}: present={bool(value)}, length={len(value) if value else 0}")  
PY  
  
