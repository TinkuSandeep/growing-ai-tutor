from __future__ import annotations  
  
import argparse  
import csv  
import os  
import sys  
from pathlib import Path  
from urllib.parse import quote  
  
import requests  
import urllib3  
from dotenv import load_dotenv  
from requests.auth import HTTPBasicAuth  
  
  
# ============================================================  
# CONFIGURATION  
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
# BASE URL  
# ============================================================  
  
def build_base_url(instance: str) -> str:  
  
    instance = instance.strip().upper()  
  
    if instance not in ALLOWED_INSTANCES:  
        raise ValueError(  
            f"Unsupported AutoSys instance: {instance}"  
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
  
        self.session.auth = HTTPBasicAuth(  
            username,  
            credential,  
        )  
  
        self.session.headers.update(  
            {  
                "Accept": "application/json"  
            }  
        )  
  
        if not verify_ssl:  
            urllib3.disable_warnings(  
                urllib3.exceptions.InsecureRequestWarning  
            )  
  
    # ========================================================  
    # REQUEST  
    # ========================================================  
  
    def _request(  
        self,  
        url: str,  
        params: dict | None = None,  
    ) -> dict:  
  
        try:  
  
            response = self.session.get(  
                url,  
                params=params,  
                timeout=TIMEOUT_SECONDS,  
                verify=self.verify_ssl,  
            )  
  
        except requests.exceptions.Timeout as exc:  
  
            raise RuntimeError(  
                "AEWS request timed out."  
            ) from exc  
  
        except requests.exceptions.ConnectionError as exc:  
  
            raise RuntimeError(  
                "Unable to connect to AEWS."  
            ) from exc  
  
        except requests.exceptions.RequestException as exc:  
  
            raise RuntimeError(  
                f"AEWS request failed: {exc}"  
            ) from exc  
  
        print(  
            f"HTTP Status : {response.status_code}"  
        )  
  
        if response.status_code == 401:  
  
            raise RuntimeError(  
                "Authentication failed."  
            )  
  
        if response.status_code == 403:  
  
            raise RuntimeError(  
                "AEWS authorization failed."  
            )  
  
        if response.status_code == 404:  
  
            raise RuntimeError(  
                "AEWS returned HTTP 404. "  
                "The wildcard job-search URL may not "  
                "be supported by this AEWS installation."  
            )  
  
        if response.status_code != 200:  
  
            raise RuntimeError(  
                f"AEWS returned HTTP "  
                f"{response.status_code}: "  
                f"{response.text[:1000]}"  
            )  
  
        try:  
  
            return response.json()  
  
        except ValueError as exc:  
  
            raise RuntimeError(  
                "AEWS returned non-JSON data."  
            ) from exc  
  
    # ========================================================  
    # FIND APPLICATION JOBS  
    # ========================================================  
  
    def find_application_jobs(  
        self,  
        instance: str,  
        application: str,  
    ) -> list[dict]:  
  
        instance = instance.strip().upper()  
        application = application.strip().upper()  
  
        base_url = build_base_url(  
            instance  
        )  
  
        # ----------------------------------------------------  
        # Discovery pattern  
        #  
        # ODIN jobs observed in AutoSys use ODIN_ prefix.  
        #  
        # We use the prefix only to reduce the search space.  
        # Final membership is still validated using the  
        # returned "application" field.  
        # ----------------------------------------------------  
  
        job_pattern = f"{application}_*"  
  
        encoded_pattern = quote(  
            job_pattern,  
            safe="*"  
        )  
  
        url = (  
            f"{base_url}/job/"  
            f"{encoded_pattern}"  
        )  
  
        params = {  
            "version": API_VERSION,  
        }  
  
        print()  
        print("=" * 72)  
        print("AUTOSYS APPLICATION JOB DISCOVERY")  
        print("=" * 72)  
  
        print(  
            f"Instance       : {instance}"  
        )  
  
        print(  
            f"Application    : {application}"  
        )  
  
        print(  
            f"Search Pattern : {job_pattern}"  
        )  
  
        print(  
            f"AEWS URL       : {url}"  
        )  
  
        print()  
  
        data = self._request(  
            url=url,  
            params=params,  
        )  
  
        # ====================================================  
        # NORMALIZE RESPONSE  
        # ====================================================  
  
        jobs = []  
  
        if isinstance(data, dict):  
  
            raw_jobs = data.get(  
                "job",  
                []  
            )  
  
            if isinstance(raw_jobs, list):  
  
                jobs = raw_jobs  
  
            elif isinstance(raw_jobs, dict):  
  
                jobs = [raw_jobs]  
  
            # Some specific-job endpoints may return  
            # the job object directly.  
  
            elif data.get("name"):  
  
                jobs = [data]  
  
        elif isinstance(data, list):  
  
            jobs = data  
  
        print()  
        print(  
            f"Jobs returned by search : {len(jobs)}"  
        )  
  
        # ====================================================  
        # APPLICATION VALIDATION  
        # ====================================================  
  
        matched_jobs = []  
  
        rejected = 0  
  
        for job in jobs:  
  
            returned_application = str(  
                job.get(  
                    "application",  
                    ""  
                )  
            ).strip().upper()  
  
            if returned_application != application:  
  
                rejected += 1  
                continue  
  
            matched_jobs.append(  
                {  
                    "application": job.get(  
                        "application",  
                        ""  
                    ),  
  
                    "scheduler_instance": instance,  
  
                    "job_name": job.get(  
                        "name",  
                        ""  
                    ),  
  
                    "job_type": job.get(  
                        "jobType",  
                        ""  
                    ),  
  
                    "box_name": job.get(  
                        "boxName",  
                        ""  
                    ),  
  
                    "description": job.get(  
                        "description",  
                        ""  
                    ),  
  
                    "machine": job.get(  
                        "machine",  
                        ""  
                    ),  
  
                    "status_code": job.get(  
                        "status",  
                        ""  
                    ),  
  
                    "status": job.get(  
                        "strStatus",  
                        ""  
                    ),  
                }  
            )  
  
        # ====================================================  
        # REMOVE DUPLICATES  
        # ====================================================  
  
        unique = {}  
  
        for job in matched_jobs:  
  
            job_name = str(  
                job.get(  
                    "job_name",  
                    ""  
                )  
            ).strip()  
  
            if not job_name:  
                continue  
  
            unique[job_name] = job  
  
        matched_jobs = list(  
            unique.values()  
        )  
  
        # ====================================================  
        # SORT  
        # ====================================================  
  
        matched_jobs.sort(  
            key=lambda job: str(  
                job.get(  
                    "job_name",  
                    ""  
                )  
            ).upper()  
        )  
  
        print()  
        print("=" * 72)  
        print("DISCOVERY RESULT")  
        print("=" * 72)  
  
        print(  
            f"Search returned : {len(jobs)}"  
        )  
  
        print(  
            f"Rejected        : {rejected}"  
        )  
  
        print(  
            f"{application} jobs       : "  
            f"{len(matched_jobs)}"  
        )  
  
        return matched_jobs  
  
  
# ============================================================  
# DISPLAY JOBS  
# ============================================================  
  
def display_jobs(  
    jobs: list[dict],  
    application: str,  
) -> None:  
  
    print()  
    print("=" * 120)  
    print(  
        f"{application} AUTOSYS JOBS"  
    )  
    print("=" * 120)  
  
    if not jobs:  
  
        print(  
            "No matching application jobs found."  
        )  
  
        return  
  
    print(  
        f"{'JOB NAME':<55}"  
        f"{'TYPE':<10}"  
        f"{'BOX NAME':<35}"  
        f"{'STATUS':<20}"  
    )  
  
    print("-" * 120)  
  
    for job in jobs:  
  
        print(  
            f"{str(job['job_name'])[:53]:<55}"  
            f"{str(job['job_type'])[:8]:<10}"  
            f"{str(job['box_name'])[:33]:<35}"  
            f"{str(job['status'])[:18]:<20}"  
        )  
  
  
# ============================================================  
# WRITE CSV  
# ============================================================  
  
def write_csv(  
    application: str,  
    instance: str,  
    jobs: list[dict],  
) -> Path:  
  
    output_directory = Path(  
        "output"  
    )  
  
    output_directory.mkdir(  
        parents=True,  
        exist_ok=True,  
    )  
  
    output_file = (  
        output_directory  
        / (  
            f"{application}_"  
            f"{instance}_"  
            f"autosys_jobs.csv"  
        )  
    )  
  
    columns = [  
        "application",  
        "scheduler_instance",  
        "job_name",  
        "job_type",  
        "box_name",  
        "description",  
        "machine",  
        "status_code",  
        "status",  
    ]  
  
    with output_file.open(  
        "w",  
        newline="",  
        encoding="utf-8-sig",  
    ) as handle:  
  
        writer = csv.DictWriter(  
            handle,  
            fieldnames=columns,  
        )  
  
        writer.writeheader()  
  
        writer.writerows(  
            jobs  
        )  
  
    return output_file  
  
  
# ============================================================  
# MAIN  
# ============================================================  
  
def main() -> int:  
  
    parser = argparse.ArgumentParser(  
        description=(  
            "Pull jobs belonging to an "  
            "AutoSys application."  
        )  
    )  
  
    parser.add_argument(  
        "--application",  
        required=True,  
    )  
  
    parser.add_argument(  
        "--instance",  
        required=True,  
    )  
  
    parser.add_argument(  
        "--no-ssl-verify",  
        action="store_true",  
    )  
  
    args = parser.parse_args()  
  
    # ========================================================  
    # LOAD .ENV  
    # ========================================================  
  
    load_dotenv(  
        override=False  
    )  
  
    username = os.getenv(  
        "AUTOSYS_API_USER"  
    )  
  
    credential = os.getenv(  
        "AUTOSYS_API_CREDENTIAL"  
    )  
  
    if not username:  
  
        print(  
            "ERROR: AUTOSYS_API_USER "  
            "not found in .env"  
        )  
  
        return 1  
  
    if not credential:  
  
        print(  
            "ERROR: AUTOSYS_API_CREDENTIAL "  
            "not found in .env"  
        )  
  
        return 1  
  
    application = (  
        args.application  
        .strip()  
        .upper()  
    )  
  
    instance = (  
        args.instance  
        .strip()  
        .upper()  
    )  
  
    print()  
    print("=" * 72)  
    print("AUTOSYS APPLICATION JOB LIST")  
    print("=" * 72)  
  
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
  
        jobs = client.find_application_jobs(  
            instance=instance,  
            application=application,  
        )  
  
        display_jobs(  
            jobs,  
            application,  
        )  
  
        output_file = write_csv(  
            application,  
            instance,  
            jobs,  
        )  
  
        print()  
        print("=" * 72)  
        print("COMPLETED")  
        print("=" * 72)  
  
        print(  
            f"Application : {application}"  
        )  
  
        print(  
            f"Instance    : {instance}"  
        )  
  
        print(  
            f"Jobs Found  : {len(jobs)}"  
        )  
  
        print(  
            f"CSV File    : "  
            f"{output_file.resolve()}"  
        )  
  
        return 0  
  
    except Exception as exc:  
  
        print()  
        print("=" * 72)  
        print("FAILED")  
        print("=" * 72)  
  
        print(  
            str(exc)  
        )  
  
        return 1  
  
  
if __name__ == "__main__":  
    sys.exit(  
        main()  
    )  
