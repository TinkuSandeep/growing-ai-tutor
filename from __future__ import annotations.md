from __future__ import annotations  
  
import argparse  
import json  
import os  
import sys  
  
import requests  
import urllib3  
from dotenv import load_dotenv  
from requests.auth import HTTPBasicAuth  
  
  
# ============================================================  
# AUTOSYS CONFIGURATION  
# Same URL pattern as working Batch Dashboard  
# ============================================================  
  
AUTOSYS_BASE_URL = (  
    "https://{instance}-autosyswebapi.wellsfargo.com/AEWS"  
)  
  
API_VERSION = 3  
TIMEOUT_SECONDS = 120  
  
ALLOWED_INSTANCES = {  
    "PB3",  
    "PC3",  
    "PG3",  
    "DB3",  
    "UB3",  
}  
  
  
# ============================================================  
# BUILD AUTOSYS URL  
# ============================================================  
  
def build_base_url(instance: str) -> str:  
  
    instance = instance.upper().strip()  
  
    if instance not in ALLOWED_INSTANCES:  
        raise ValueError(  
            f"Unsupported AutoSys instance: {instance}. "  
            f"Supported instances: "  
            f"{', '.join(sorted(ALLOWED_INSTANCES))}"  
        )  
  
    return AUTOSYS_BASE_URL.format(  
        instance=instance.lower()  
    ).rstrip("/")  
  
  
# ============================================================  
# AUTOSYS CLIENT  
# ============================================================  
  
class AutoSysClient:  
  
    def __init__(  
        self,  
        username: str,  
        credential: str,  
        verify_ssl: bool = True,  
    ):  
  
        self.verify_ssl = verify_ssl  
  
        self.session = requests.Session()  
  
        # Same authentication approach as Batch Dashboard  
        self.session.auth = HTTPBasicAuth(  
            username,  
            credential,  
        )  
  
        # Same Accept header as Batch Dashboard  
        self.session.headers.update(  
            {  
                "Accept": "application/json"  
            }  
        )  
  
        # Hide warning only when user explicitly runs  
        # with --no-ssl-verify for local testing.  
        if not verify_ssl:  
            urllib3.disable_warnings(  
                urllib3.exceptions.InsecureRequestWarning  
            )  
  
  
    # ========================================================  
    # TEST /JOB ENDPOINT  
    # ========================================================  
  
    def get_jobs(  
        self,  
        instance: str,  
        count: int = 1,  
    ):  
  
        base_url = build_base_url(  
            instance  
        )  
  
        url = f"{base_url}/job"  
  
        # Same parameters used by working Batch Dashboard  
        # health_check()  
        params = {  
            "count": count,  
            "version": API_VERSION,  
        }  
  
        print()  
        print("=" * 70)  
        print("AUTOSYS AEWS REQUEST")  
        print("=" * 70)  
  
        print(  
            f"AutoSys Instance : {instance.upper()}"  
        )  
  
        print(  
            f"AEWS URL         : {url}"  
        )  
  
        print(  
            f"API Version      : {API_VERSION}"  
        )  
  
        print(  
            f"SSL Verification : {self.verify_ssl}"  
        )  
  
        print()  
        print(  
            "Connecting to AutoSys AEWS..."  
        )  
  
        try:  
  
            response = self.session.get(  
                url,  
                params=params,  
                timeout=TIMEOUT_SECONDS,  
                verify=self.verify_ssl,  
            )  
  
        except requests.exceptions.SSLError as exc:  
  
            raise RuntimeError(  
                "SSL certificate validation failed. "  
                "Your local Python installation does not "  
                "currently trust the AutoSys corporate "  
                "certificate. For connectivity testing only, "  
                "run with --no-ssl-verify."  
            ) from exc  
  
        except requests.exceptions.ConnectTimeout as exc:  
  
            raise RuntimeError(  
                "Connection to AutoSys AEWS timed out."  
            ) from exc  
  
        except requests.exceptions.ReadTimeout as exc:  
  
            raise RuntimeError(  
                "Connected to AutoSys AEWS, but the "  
                "server did not respond before timeout."  
            ) from exc  
  
        except requests.exceptions.ConnectionError as exc:  
  
            raise RuntimeError(  
                "Unable to connect to AutoSys AEWS."  
            ) from exc  
  
        except requests.exceptions.RequestException as exc:  
  
            raise RuntimeError(  
                f"AutoSys request failed: {exc}"  
            ) from exc  
  
        print(  
            f"HTTP Status      : {response.status_code}"  
        )  
  
        if response.status_code == 401:  
  
            raise RuntimeError(  
                "HTTP 401 - AutoSys authentication failed. "  
                "Check AUTOSYS_API_USER and "  
                "AUTOSYS_API_CREDENTIAL."  
            )  
  
        if response.status_code == 403:  
  
            raise RuntimeError(  
                "HTTP 403 - Authentication succeeded, "  
                "but this account is not authorized "  
                "for the AEWS endpoint."  
            )  
  
        if response.status_code != 200:  
  
            raise RuntimeError(  
                f"AutoSys returned HTTP "  
                f"{response.status_code}: "  
                f"{response.text[:500]}"  
            )  
  
        print(  
            "AEWS connection successful."  
        )  
  
        try:  
  
            return response.json()  
  
        except ValueError as exc:  
  
            raise RuntimeError(  
                "AEWS returned HTTP 200 but the "  
                "response was not valid JSON."  
            ) from exc  
  
  
# ============================================================  
# DISPLAY RESPONSE  
# ============================================================  
  
def display_response(data) -> None:  
  
    print()  
    print("=" * 70)  
    print("AEWS RESPONSE")  
    print("=" * 70)  
  
    print(  
        json.dumps(  
            data,  
            indent=2,  
            default=str,  
        )[:5000]  
    )  
  
  
# ============================================================  
# MAIN  
# ============================================================  
  
def main() -> int:  
  
    parser = argparse.ArgumentParser(  
        description=(  
            "AutoSys application job-list utility."  
        )  
    )  
  
    parser.add_argument(  
        "--application",  
        required=True,  
        help=(  
            "AutoSys application name. "  
            "Example: ODIN"  
        ),  
    )  
  
    parser.add_argument(  
        "--instance",  
        required=True,  
        help=(  
            "AutoSys instance. "  
            "Example: PB3"  
        ),  
    )  
  
    parser.add_argument(  
        "--no-ssl-verify",  
        action="store_true",  
        help=(  
            "Disable SSL certificate verification "  
            "for local connectivity testing only."  
        ),  
    )  
  
    args = parser.parse_args()  
  
    # --------------------------------------------------------  
    # Load .env  
    # --------------------------------------------------------  
  
    load_dotenv(  
        override=False  
    )  
  
    username = os.getenv(  
        "AUTOSYS_API_USER"  
    )  
  
    credential = os.getenv(  
        "AUTOSYS_API_CREDENTIAL"  
    )  
  
    # --------------------------------------------------------  
    # Validate environment  
    # --------------------------------------------------------  
  
    if not username:  
  
        print()  
        print(  
            "ERROR: AUTOSYS_API_USER "  
            "was not found in .env."  
        )  
  
        return 1  
  
    if not credential:  
  
        print()  
        print(  
            "ERROR: AUTOSYS_API_CREDENTIAL "  
            "was not found in .env."  
        )  
  
        return 1  
  
    instance = (  
        args.instance  
        .upper()  
        .strip()  
    )  
  
    application = (  
        args.application  
        .strip()  
    )  
  
    print()  
    print("=" * 70)  
    print("AUTOSYS APPLICATION JOB LIST")  
    print("=" * 70)  
  
    print(  
        f"Application      : {application}"  
    )  
  
    print(  
        f"AutoSys Instance : {instance}"  
    )  
  
    try:  
  
        client = AutoSysClient(  
            username=username,  
            credential=credential,  
            verify_ssl=not args.no_ssl_verify,  
        )  
  
        # ----------------------------------------------------  
        # IMPORTANT  
        #  
        # Connectivity validation first.  
        #  
        # This calls the exact /job endpoint pattern already  
        # proven by the Batch Dashboard health_check().  
        #  
        # count=1 deliberately prevents a broad job pull.  
        # ----------------------------------------------------  
  
        data = client.get_jobs(  
            instance=instance,  
            count=1,  
        )  
  
        display_response(  
            data  
        )  
  
        print()  
        print("=" * 70)  
        print("CONNECTIVITY TEST SUCCESSFUL")  
        print("=" * 70)  
  
        print()  
        print(  
            f"Application requested : {application}"  
        )  
  
        print(  
            "AEWS /job endpoint     : WORKING"  
        )  
  
        print()  
        print(  
            "NOTE: This test deliberately requested "  
            "only one job."  
        )  
  
        print(  
            "The ODIN application filter has not "  
            "been applied yet."  
        )  
  
        return 0  
  
    except Exception as exc:  
  
        print()  
        print("=" * 70)  
        print("FAILED")  
        print("=" * 70)  
  
        print()  
        print(  
            str(exc)  
        )  
  
        return 1  
  
  
if __name__ == "__main__":  
    sys.exit(  
        main()  
    )  
