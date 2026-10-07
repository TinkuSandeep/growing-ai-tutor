from __future__ import annotations  
  
import argparse  
import csv  
import os  
import sys  
from pathlib import Path  
from urllib.parse import urljoin  
  
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
  
# Start conservatively. If AEWS accepts a larger page size,  
# you can increase this later.  
PAGE_SIZE = 100  
  
ALLOWED_INSTANCES = {  
    "PB3",  
    "PC3",  
    "PG3",  
    "DB3",  
    "UB3",  
}  
  
  
# ============================================================  
# BUILD BASE URL  
# ============================================================  
  
def build_base_url(instance: str) -> str:  
  
    instance = instance.strip().upper()  
  
    if instance not in ALLOWED_INSTANCES:  
        raise ValueError(  
            f"Unsupported AutoSys instance: {instance}. "  
            f"Supported: {', '.join(sorted(ALLOWED_INSTANCES))}"  
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
                "Accept": "application/json",  
            }  
        )  
  
        if not verify_ssl:  
            urllib3.disable_warnings(  
                urllib3.exceptions.InsecureRequestWarning  
            )  
  
    # ========================================================  
    # GET APPLICATION JOBS  
    # ========================================================  
  
    def get_application_jobs(  
        self,  
        instance: str,  
        application: str,  
    ) -> list[dict]:  
  
        instance = instance.strip().upper()  
        application = application.strip().upper()  
  
        base_url = build_base_url(instance)  
  
        url = f"{base_url}/job"  
  
        params = {  
            "count": PAGE_SIZE,  
            "version": API_VERSION,  
        }  
  
        matched_jobs = []  
  
        page_number = 0  
        jobs_scanned = 0  
  
        # Protect against a broken pagination loop.  
        visited_urls = set()  
  
        print()  
        print("=" * 72)  
        print("AUTOSYS APPLICATION JOB DISCOVERY")  
        print("=" * 72)  
  
        print(f"Instance       : {instance}")  
        print(f"Application    : {application}")  
        print(f"API Version    : {API_VERSION}")  
        print(f"Page Size      : {PAGE_SIZE}")  
        print(f"SSL Verify     : {self.verify_ssl}")  
  
        print()  
        print("Starting AEWS job discovery...")  
        print()  
  
        while url:  
  
            page_number += 1  
  
            print(  
                f"Reading page {page_number}..."  
            )  
  
            try:  
  
                response = self.session.get(  
                    url=url,  
                    params=params,  
                    timeout=TIMEOUT_SECONDS,  
                    verify=self.verify_ssl,  
                )  
  
            except requests.exceptions.SSLError as exc:  
  
                raise RuntimeError(  
                    "SSL certificate validation failed. "  
                    "For local testing you can use "  
                    "--no-ssl-verify."  
                ) from exc  
  
            except requests.exceptions.ConnectTimeout as exc:  
  
                raise RuntimeError(  
                    "Connection to AutoSys AEWS timed out."  
                ) from exc  
  
            except requests.exceptions.ReadTimeout as exc:  
  
                raise RuntimeError(  
                    "AutoSys AEWS did not respond "  
                    "before the timeout."  
                ) from exc  
  
            except requests.exceptions.ConnectionError as exc:  
  
                raise RuntimeError(  
                    "Unable to connect to AutoSys AEWS."  
                ) from exc  
  
            except requests.exceptions.RequestException as exc:  
  
                raise RuntimeError(  
                    f"AEWS request failed: {exc}"  
                ) from exc  
  
            # ------------------------------------------------  
            # HTTP STATUS CHECK  
            # ------------------------------------------------  
  
            if response.status_code == 401:  
  
                raise RuntimeError(  
                    "HTTP 401 - Authentication failed. "  
                    "Check AUTOSYS_API_USER and "  
                    "AUTOSYS_API_CREDENTIAL."  
                )  
  
            if response.status_code == 403:  
  
                raise RuntimeError(  
                    "HTTP 403 - Account does not have "  
                    "permission to access AEWS."  
                )  
  
            if response.status_code != 200:  
  
                raise RuntimeError(  
                    f"AEWS returned HTTP "  
                    f"{response.status_code}: "  
                    f"{response.text[:500]}"  
                )  
  
            # ------------------------------------------------  
            # JSON RESPONSE  
            # ------------------------------------------------  
  
            try:  
  
                data = response.json()  
  
            except ValueError as exc:  
  
                raise RuntimeError(  
                    "AEWS returned invalid JSON."  
                ) from exc  
  
            # ------------------------------------------------  
            # JOB COLLECTION  
            # ------------------------------------------------  
  
            jobs = data.get(  
                "job",  
                []  
            )  
  
            if isinstance(jobs, dict):  
                jobs = [jobs]  
  
            if not isinstance(jobs, list):  
                raise RuntimeError(  
                    "Unexpected AEWS response. "  
                    "'job' is not a list."  
                )  
  
            jobs_scanned += len(jobs)  
  
            page_matches = 0  
  
            for job in jobs:  
  
                job_application = str(  
                    job.get(  
                        "application",  
                        ""  
                    )  
                ).strip().upper()  
  
                # --------------------------------------------  
                # ONLY REQUESTED APPLICATION  
                # --------------------------------------------  
  
                if job_application != application:  
                    continue  
  
                page_matches += 1  
  
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
  
            print(  
                f"  Jobs scanned : {len(jobs)}"  
            )  
  
            print(  
                f"  {application} matches : "  
                f"{page_matches}"  
            )  
  
            # ------------------------------------------------  
            # NEXT PAGE  
            # ------------------------------------------------  
  
            next_object = data.get(  
                "next"  
            )  
  
            next_href = None  
  
            if isinstance(  
                next_object,  
                dict  
            ):  
                next_href = next_object.get(  
                    "href"  
                )  
  
            if not next_href:  
  
                print()  
                print(  
                    "No additional AEWS pages."  
                )  
  
                break  
  
            # AEWS normally returns an absolute href,  
            # but urljoin also handles relative hrefs safely.  
  
            next_url = urljoin(  
                response.url,  
                next_href  
            )  
  
            # Prevent accidental infinite loop.  
  
            if next_url in visited_urls:  
  
                raise RuntimeError(  
                    "AEWS pagination returned a URL "  
                    "that has already been processed."  
                )  
  
            visited_urls.add(  
                next_url  
            )  
  
            url = next_url  
  
            # IMPORTANT:  
            # next.href already contains count/version/index.  
            # Do not append the original params again.  
  
            params = None  
  
        # ====================================================  
        # REMOVE DUPLICATES  
        # ====================================================  
  
        unique_jobs = {}  
  
        for job in matched_jobs:  
  
            key = (  
                job["scheduler_instance"],  
                job["job_name"],  
            )  
  
            unique_jobs[key] = job  
  
        matched_jobs = list(  
            unique_jobs.values()  
        )  
  
        # ====================================================  
        # SORT RESULTS  
        # ====================================================  
  
        matched_jobs.sort(  
            key=lambda item: (  
                str(  
                    item.get(  
                        "box_name",  
                        ""  
                    )  
                ).upper(),  
  
                str(  
                    item.get(  
                        "job_name",  
                        ""  
                    )  
                ).upper(),  
            )  
        )  
  
        print()  
        print("=" * 72)  
        print("DISCOVERY COMPLETE")  
        print("=" * 72)  
  
        print(  
            f"Pages Read      : {page_number}"  
        )  
  
        print(  
            f"Jobs Scanned    : {jobs_scanned}"  
        )  
  
        print(  
            f"{application} Jobs      : "  
            f"{len(matched_jobs)}"  
        )  
  
        return matched_jobs  
  
  
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
  
    filename = (  
        f"{application.upper()}_"  
        f"{instance.upper()}_"  
        f"autosys_jobs.csv"  
    )  
  
    output_file = (  
        output_directory  
        / filename  
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
        mode="w",  
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
# DISPLAY RESULTS  
# ============================================================  
  
def display_jobs(  
    jobs: list[dict],  
    application: str,  
) -> None:  
  
    print()  
    print("=" * 110)  
    print(  
        f"{application.upper()} JOBS"  
    )  
    print("=" * 110)  
  
    if not jobs:  
  
        print(  
            "No matching jobs found."  
        )  
  
        return  
  
    print(  
        f"{'JOB NAME':<45}"  
        f"{'TYPE':<10}"  
        f"{'BOX NAME':<35}"  
        f"{'STATUS':<20}"  
    )  
  
    print("-" * 110)  
  
    for job in jobs:  
  
        job_name = str(  
            job.get(  
                "job_name",  
                ""  
            )  
        )[:43]  
  
        job_type = str(  
            job.get(  
                "job_type",  
                ""  
            )  
        )[:8]  
  
        box_name = str(  
            job.get(  
                "box_name",  
                ""  
            )  
        )[:33]  
  
        status = str(  
            job.get(  
                "status",  
                ""  
            )  
        )[:18]  
  
        print(  
            f"{job_name:<45}"  
            f"{job_type:<10}"  
            f"{box_name:<35}"  
            f"{status:<20}"  
        )  
  
  
# ============================================================  
# MAIN  
# ============================================================  
  
def main() -> int:  
  
    parser = argparse.ArgumentParser(  
        description=(  
            "Pull AutoSys jobs belonging "  
            "to a specific application."  
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
            "AutoSys scheduler instance. "  
            "Example: PB3"  
        ),  
    )  
  
    parser.add_argument(  
        "--no-ssl-verify",  
        action="store_true",  
        help=(  
            "Disable SSL verification "  
            "for local testing only."  
        ),  
    )  
  
    args = parser.parse_args()  
  
    # ========================================================  
    # LOAD LOCAL ENVIRONMENT  
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
  
    # ========================================================  
    # VALIDATION  
    # ========================================================  
  
    if not username:  
  
        print(  
            "ERROR: AUTOSYS_API_USER "  
            "was not found in .env"  
        )  
  
        return 1  
  
    if not credential:  
  
        print(  
            "ERROR: AUTOSYS_API_CREDENTIAL "  
            "was not found in .env"  
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
  
        # ====================================================  
        # CREATE CLIENT  
        # ====================================================  
  
        client = AutoSysClient(  
            username=username,  
            credential=credential,  
            verify_ssl=not args.no_ssl_verify,  
        )  
  
        # ====================================================  
        # DISCOVER JOBS  
        # ====================================================  
  
        jobs = client.get_application_jobs(  
            instance=instance,  
            application=application,  
        )  
  
        # ====================================================  
        # DISPLAY JOBS  
        # ====================================================  
  
        display_jobs(  
            jobs=jobs,  
            application=application,  
        )  
  
        # ====================================================  
        # CREATE CSV  
        # ====================================================  
  
        output_file = write_csv(  
            application=application,  
            instance=instance,  
            jobs=jobs,  
        )  
  
        # ====================================================  
        # FINAL RESULT  
        # ====================================================  
  
        print()  
        print("=" * 72)  
        print("COMPLETED")  
        print("=" * 72)  
  
        print(  
            f"Application      : {application}"  
        )  
  
        print(  
            f"AutoSys Instance : {instance}"  
        )  
  
        print(  
            f"Jobs Found       : {len(jobs)}"  
        )  
  
        print(  
            f"CSV File         : "  
            f"{output_file.resolve()}"  
        )  
  
        if not jobs:  
  
            print()  
            print(  
                "WARNING: AEWS was reachable, "  
                f"but no jobs with application='{application}' "  
                "were found."  
            )  
  
            return 2  
  
        return 0  
  
    except Exception as exc:  
  
        print()  
        print("=" * 72)  
        print("FAILED")  
        print("=" * 72)  
  
        print()  
        print(  
            str(exc)  
        )  
  
        return 1  
  
  
if __name__ == "__main__":  
    sys.exit(  
        main()  
    )  
