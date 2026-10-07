from __future__ import annotations  
  
import argparse  
import csv  
import os  
import re  
import sys  
from pathlib import Path  
  
import requests  
from dotenv import load_dotenv  
from requests.auth import HTTPBasicAuth  
  
  
# ============================================================  
# AUTOSYS AEWS CONFIGURATION  
# ============================================================  
#  
# Replace these URLs with the SAME AEWS URLs already working  
# in your Batch Transformation / Batch Dashboard automation.  
#  
# Example:  
# "PB3": "https://your-pb3-host:9443/AEWS"  
#  
# ============================================================  
  
AUTOSYS_INSTANCES = {  
    "PB3": "https://<PB3_AEWS_HOST>:9443/AEWS",  
    "PC3": "https://<PC3_AEWS_HOST>:9443/AEWS",  
    "PG3": "https://<PG3_AEWS_HOST>:9443/AEWS",  
    "DB3": "https://<DB3_AEWS_HOST>:9443/AEWS",  
    "UB3": "https://<UB3_AEWS_HOST>:9443/AEWS",  
}  
  
  
# ============================================================  
# GET ALL JIL FROM AUTOSYS  
# ============================================================  
  
def get_all_jil(  
    instance: str,  
    username: str,  
    password: str,  
    verify_ssl: bool = True,  
) -> str:  
  
    instance = instance.upper().strip()  
  
    if instance not in AUTOSYS_INSTANCES:  
        supported = ", ".join(AUTOSYS_INSTANCES.keys())  
  
        raise ValueError(  
            f"Unsupported AutoSys instance: {instance}. "  
            f"Supported instances: {supported}"  
        )  
  
    base_url = AUTOSYS_INSTANCES[instance].rstrip("/")  
  
    url = f"{base_url}/jil/job"  
  
    params = {  
        "name": "ALL",  
        "timeout": "300",  
    }  
  
    print("=" * 70)  
    print("AUTOSYS APPLICATION JOB LIST")  
    print("=" * 70)  
    print()  
    print(f"AutoSys Instance : {instance}")  
    print(f"AEWS URL         : {url}")  
    print()  
    print("Connecting to AutoSys AEWS...")  
    print("Retrieving AutoSys job definitions...")  
  
    try:  
  
        response = requests.get(  
            url=url,  
            params=params,  
            auth=HTTPBasicAuth(  
                username,  
                password,  
            ),  
            headers={  
                "Accept": "text/plain",  
            },  
            timeout=300,  
            verify=verify_ssl,  
        )  
  
        response.raise_for_status()  
  
        print("AutoSys API connection successful.")  
        print()  
  
        return response.text  
  
    except requests.exceptions.SSLError as exc:  
  
        raise RuntimeError(  
            "SSL certificate validation failed. "  
            "If this is only a local test and your internal "  
            "AutoSys certificate is not trusted by Python, "  
            "you can test with --no-ssl-verify. "  
            "Do not use disabled SSL verification for production."  
        ) from exc  
  
    except requests.exceptions.HTTPError as exc:  
  
        status_code = (  
            exc.response.status_code  
            if exc.response is not None  
            else "UNKNOWN"  
        )  
  
        if status_code == 401:  
            raise RuntimeError(  
                "AutoSys returned HTTP 401. "  
                "Check AUTOSYS_API_USER and "  
                "AUTOSYS_API_PASSWORD."  
            ) from exc  
  
        if status_code == 403:  
            raise RuntimeError(  
                "AutoSys returned HTTP 403. "  
                "The account authenticated but may not "  
                "have permission to access AEWS JIL."  
            ) from exc  
  
        if status_code == 404:  
            raise RuntimeError(  
                f"AutoSys returned HTTP 404 for {url}. "  
                "Check the AEWS base URL and confirm that "  
                "the JIL endpoint is available in this environment."  
            ) from exc  
  
        raise RuntimeError(  
            f"AutoSys returned HTTP {status_code}: {exc}"  
        ) from exc  
  
    except requests.exceptions.Timeout as exc:  
  
        raise RuntimeError(  
            "AutoSys API request timed out."  
        ) from exc  
  
    except requests.exceptions.ConnectionError as exc:  
  
        raise RuntimeError(  
            "Unable to connect to AutoSys AEWS. "  
            "Check hostname, VPN/network access and port."  
        ) from exc  
  
    except requests.exceptions.RequestException as exc:  
  
        raise RuntimeError(  
            f"AutoSys API request failed: {exc}"  
        ) from exc  
  
  
# ============================================================  
# SPLIT COMPLETE JIL INTO INDIVIDUAL JOB DEFINITIONS  
# ============================================================  
  
def split_jobs(jil_text: str) -> list[str]:  
  
    if not jil_text:  
        return []  
  
    # Each AutoSys job definition normally starts with:  
    #  
    # insert_job: JOB_NAME job_type: CMD  
    #  
    # or  
    #  
    # insert_job: BOX_NAME job_type: BOX  
  
    sections = re.split(  
        r"(?=^\s*insert_job\s*:)",  
        jil_text,  
        flags=re.IGNORECASE | re.MULTILINE,  
    )  
  
    jobs = []  
  
    for section in sections:  
  
        section = section.strip()  
  
        if not section:  
            continue  
  
        if re.match(  
            r"^\s*insert_job\s*:",  
            section,  
            flags=re.IGNORECASE,  
        ):  
            jobs.append(section)  
  
    return jobs  
  
  
# ============================================================  
# READ JIL ATTRIBUTE  
# ============================================================  
  
def get_attribute(  
    job_text: str,  
    attribute: str,  
) -> str | None:  
  
    pattern = (  
        rf"(?im)^\s*"  
        rf"{re.escape(attribute)}"  
        rf"\s*:\s*(.*?)\s*$"  
    )  
  
    match = re.search(  
        pattern,  
        job_text,  
    )  
  
    if not match:  
        return None  
  
    value = match.group(1).strip()  
  
    # Remove surrounding quotes if present.  
  
    if (  
        len(value) >= 2  
        and value[0] == '"'  
        and value[-1] == '"'  
    ):  
        value = value[1:-1].strip()  
  
    return value or None  
  
  
# ============================================================  
# GET JOB NAME  
# ============================================================  
  
def get_job_name(  
    job_text: str,  
) -> str | None:  
  
    match = re.search(  
        r"(?im)^\s*insert_job\s*:\s*([^\s]+)",  
        job_text,  
    )  
  
    if not match:  
        return None  
  
    return match.group(1).strip()  
  
  
# ============================================================  
# GET JOB TYPE  
# ============================================================  
  
def get_job_type(  
    job_text: str,  
) -> str | None:  
  
    # job_type may appear on the insert_job line:  
    #  
    # insert_job: TEST_JOB job_type: CMD  
  
    match = re.search(  
        r"(?im)^\s*insert_job\s*:.*?"  
        r"\bjob_type\s*:\s*([^\s]+)",  
        job_text,  
    )  
  
    if match:  
        return match.group(1).strip()  
  
    # Or potentially on a separate line.  
  
    return get_attribute(  
        job_text,  
        "job_type",  
    )  
  
  
# ============================================================  
# FIND ALL JOBS FOR APPLICATION  
# ============================================================  
  
def get_application_jobs(  
    jil_text: str,  
    application_name: str,  
    instance: str,  
) -> list[dict]:  
  
    requested_application = (  
        application_name  
        .strip()  
        .casefold()  
    )  
  
    all_jobs = split_jobs(  
        jil_text  
    )  
  
    print(  
        f"Total AutoSys definitions retrieved: "  
        f"{len(all_jobs)}"  
    )  
  
    results = []  
  
    for job_text in all_jobs:  
  
        application = get_attribute(  
            job_text,  
            "application",  
        )  
  
        if not application:  
            continue  
  
        # Exact application match.  
        #  
        # Case insensitive:  
        #  
        # ODIN == odin  
        #  
        # But:  
        #  
        # ODIN != ODIN_TEST  
  
        if application.strip().casefold() != requested_application:  
            continue  
  
        job_name = get_job_name(  
            job_text  
        )  
  
        if not job_name:  
            continue  
  
        job_type = get_job_type(  
            job_text  
        )  
  
        box_name = get_attribute(  
            job_text,  
            "box_name",  
        )  
  
        machine = get_attribute(  
            job_text,  
            "machine",  
        )  
  
        owner = get_attribute(  
            job_text,  
            "owner",  
        )  
  
        group = get_attribute(  
            job_text,  
            "group",  
        )  
  
        description = get_attribute(  
            job_text,  
            "description",  
        )  
  
        condition = get_attribute(  
            job_text,  
            "condition",  
        )  
  
        date_conditions = get_attribute(  
            job_text,  
            "date_conditions",  
        )  
  
        days_of_week = get_attribute(  
            job_text,  
            "days_of_week",  
        )  
  
        start_times = get_attribute(  
            job_text,  
            "start_times",  
        )  
  
        results.append(  
            {  
                "application": application,  
                "scheduler_instance": instance,  
                "job_name": job_name,  
                "job_type": job_type,  
                "box_name": box_name,  
                "machine": machine,  
                "owner": owner,  
                "group": group,  
                "description": description,  
                "condition": condition,  
                "date_conditions": date_conditions,  
                "days_of_week": days_of_week,  
                "start_times": start_times,  
            }  
        )  
  
    # Sort by box first and then job name.  
  
    return sorted(  
        results,  
        key=lambda item: (  
            (item["box_name"] or "").casefold(),  
            item["job_name"].casefold(),  
        ),  
    )  
  
  
# ============================================================  
# DISPLAY RESULTS  
# ============================================================  
  
def display_jobs(  
    jobs: list[dict],  
) -> None:  
  
    if not jobs:  
        return  
  
    print()  
    print("-" * 100)  
  
    print(  
        f"{'JOB NAME':<50}"  
        f"{'TYPE':<10}"  
        f"{'BOX NAME':<40}"  
    )  
  
    print("-" * 100)  
  
    for job in jobs:  
  
        job_name = (  
            job["job_name"] or ""  
        )  
  
        job_type = (  
            job["job_type"] or ""  
        )  
  
        box_name = (  
            job["box_name"] or ""  
        )  
  
        print(  
            f"{job_name:<50}"  
            f"{job_type:<10}"  
            f"{box_name:<40}"  
        )  
  
    print("-" * 100)  
  
  
# ============================================================  
# WRITE CSV  
# ============================================================  
  
def write_csv(  
    application_name: str,  
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
  
    safe_application = re.sub(  
        r"[^A-Za-z0-9_.-]+",  
        "_",  
        application_name,  
    )  
  
    filename = (  
        f"{safe_application}_"  
        f"{instance}_"  
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
        "machine",  
        "owner",  
        "group",  
        "description",  
        "condition",  
        "date_conditions",  
        "days_of_week",  
        "start_times",  
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
# MAIN  
# ============================================================  
  
def main() -> int:  
  
    parser = argparse.ArgumentParser(  
        description=(  
            "Pull all AutoSys jobs belonging "  
            "to a specified application."  
        )  
    )  
  
    parser.add_argument(  
        "--application",  
        required=True,  
        help=(  
            "AutoSys application attribute. "  
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
            "Disable SSL verification for "  
            "local troubleshooting only."  
        ),  
    )  
  
    args = parser.parse_args()  
  
    # --------------------------------------------------------  
    # Load local .env  
    # --------------------------------------------------------  
  
    load_dotenv(  
        override=False  
    )  
  
    username = os.getenv(  
        "AUTOSYS_API_USER"  
    )  
  
    password = os.getenv(  
        "AUTOSYS_API_PASSWORD"  
    )  
  
    # --------------------------------------------------------  
    # Validate credentials  
    # --------------------------------------------------------  
  
    if not username:  
  
        print(  
            "ERROR: AUTOSYS_API_USER "  
            "was not found in .env."  
        )  
  
        return 1  
  
    if not password:  
  
        print(  
            "ERROR: AUTOSYS_API_PASSWORD "  
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
  
    try:  
  
        # ----------------------------------------------------  
        # Retrieve complete JIL  
        # ----------------------------------------------------  
  
        jil_text = get_all_jil(  
            instance=instance,  
            username=username,  
            password=password,  
            verify_ssl=not args.no_ssl_verify,  
        )  
  
        # ----------------------------------------------------  
        # Find application jobs  
        # ----------------------------------------------------  
  
        jobs = get_application_jobs(  
            jil_text=jil_text,  
            application_name=application,  
            instance=instance,  
        )  
  
        print()  
        print("=" * 70)  
        print("RESULT")  
        print("=" * 70)  
  
        print(  
            f"Application      : {application}"  
        )  
  
        print(  
            f"AutoSys Instance : {instance}"  
        )  
  
        print(  
            f"Jobs Found       : {len(jobs)}"  
        )  
  
        # ----------------------------------------------------  
        # No jobs  
        # ----------------------------------------------------  
  
        if not jobs:  
  
            print()  
            print(  
                "No AutoSys jobs were found with:"  
            )  
  
            print(  
                f"application: {application}"  
            )  
  
            print()  
            print(  
                "Check that the application value "  
                "matches the JIL application attribute."  
            )  
  
            return 2  
  
        # ----------------------------------------------------  
        # Display jobs  
        # ----------------------------------------------------  
  
        display_jobs(  
            jobs  
        )  
  
        # ----------------------------------------------------  
        # Export CSV  
        # ----------------------------------------------------  
  
        output_file = write_csv(  
            application_name=application,  
            instance=instance,  
            jobs=jobs,  
        )  
  
        print()  
        print(  
            f"CSV created successfully:"  
        )  
  
        print(  
            output_file.resolve()  
        )  
  
        print()  
        print(  
            "Completed successfully."  
        )  
  
        return 0  
  
    except Exception as exc:  
  
        print()  
        print("=" * 70)  
        print("FAILED")  
        print("=" * 70)  
  
        print(  
            str(exc)  
        )  
  
        return 1  
  
  
if __name__ == "__main__":  
    sys.exit(  
        main()  
    )  
