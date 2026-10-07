import argparse  
import csv  
import os  
import re  
import sys  
from pathlib import Path  
  
import requests  
from dotenv import load_dotenv  
from requests.auth import HTTPBasicAuth  
  
  
# ---------------------------------------------------------  
# AutoSys API configuration  
# ---------------------------------------------------------  
  
AUTOSYS_INSTANCES = {  
    "PB3": "https://<PB3_AEWS_HOST>:9443/AEWS",  
    "PC3": "https://<PC3_AEWS_HOST>:9443/AEWS",  
    "PG3": "https://<PG3_AEWS_HOST>:9443/AEWS",  
    "DB3": "https://<DB3_AEWS_HOST>:9443/AEWS",  
    "UB3": "https://<UB3_AEWS_HOST>:9443/AEWS",  
}  
  
  
# ---------------------------------------------------------  
# Get full JIL from AutoSys  
# ---------------------------------------------------------  
  
def get_all_jil(instance, username, access_key, verify_ssl=True):  
  
    instance = instance.upper()  
  
    if instance not in AUTOSYS_INSTANCES:  
        raise ValueError(  
            f"Unsupported AutoSys instance: {instance}"  
        )  
  
    base_url = AUTOSYS_INSTANCES[instance]  
  
    url = f"{base_url}/jil/job"  
  
    params = {  
        "name": "ALL",  
        "timeout": "300"  
    }  
  
    print(f"Connecting to AutoSys instance: {instance}")  
    print("Retrieving AutoSys job definitions...")  
  
    response = requests.get(  
        url,  
        params=params,  
        auth=HTTPBasicAuth(username, access_key),  
        timeout=300,  
        verify=verify_ssl,  
        headers={  
            "Accept": "text/plain"  
        }  
    )  
  
    response.raise_for_status()  
  
    return response.text  
  
  
# ---------------------------------------------------------  
# Split JIL into individual jobs  
# ---------------------------------------------------------  
  
def split_jobs(jil_text):  
  
    pattern = r"(?=insert_job\s*:)"  
  
    sections = re.split(  
        pattern,  
        jil_text,  
        flags=re.IGNORECASE  
    )  
  
    return [  
        section.strip()  
        for section in sections  
        if section.strip().lower().startswith("insert_job")  
    ]  
  
  
# ---------------------------------------------------------  
# Read a JIL attribute  
# ---------------------------------------------------------  
  
def get_attribute(job_text, attribute):  
  
    pattern = rf"(?im)^\s*{re.escape(attribute)}\s*:\s*(.*?)\s*$"  
  
    match = re.search(  
        pattern,  
        job_text  
    )  
  
    if match:  
        return match.group(1).strip()  
  
    return None  
  
  
# ---------------------------------------------------------  
# Read job name and job type  
# ---------------------------------------------------------  
  
def get_job_header(job_text):  
  
    pattern = (  
        r"(?im)^\s*insert_job\s*:\s*([^\s]+)"  
        r".*?"  
        r"job_type\s*:\s*([^\s]+)"  
    )  
  
    match = re.search(  
        pattern,  
        job_text  
    )  
  
    if match:  
        return (  
            match.group(1).strip(),  
            match.group(2).strip()  
        )  
  
    # Some environments may format job_type on another line.  
    name_match = re.search(  
        r"(?im)^\s*insert_job\s*:\s*([^\s]+)",  
        job_text  
    )  
  
    type_match = re.search(  
        r"(?im)^\s*job_type\s*:\s*([^\s]+)",  
        job_text  
    )  
  
    job_name = (  
        name_match.group(1).strip()  
        if name_match  
        else None  
    )  
  
    job_type = (  
        type_match.group(1).strip()  
        if type_match  
        else None  
    )  
  
    return job_name, job_type  
  
  
# ---------------------------------------------------------  
# Filter jobs by application  
# ---------------------------------------------------------  
  
def get_application_jobs(  
    jil_text,  
    application_name,  
    instance  
):  
  
    application_name = application_name.strip()  
  
    jobs = split_jobs(  
        jil_text  
    )  
  
    results = []  
  
    for job_text in jobs:  
  
        application = get_attribute(  
            job_text,  
            "application"  
        )  
  
        if not application:  
            continue  
  
        if application.lower() != application_name.lower():  
            continue  
  
        job_name, job_type = get_job_header(  
            job_text  
        )  
  
        if not job_name:  
            continue  
  
        box_name = get_attribute(  
            job_text,  
            "box_name"  
        )  
  
        machine = get_attribute(  
            job_text,  
            "machine"  
        )  
  
        owner = get_attribute(  
            job_text,  
            "owner"  
        )  
  
        group = get_attribute(  
            job_text,  
            "group"  
        )  
  
        description = get_attribute(  
            job_text,  
            "description"  
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
            }  
        )  
  
    return sorted(  
        results,  
        key=lambda x: x["job_name"].lower()  
    )  
  
  
# ---------------------------------------------------------  
# Write CSV  
# ---------------------------------------------------------  
  
def write_csv(  
    application_name,  
    instance,  
    jobs  
):  
  
    output_dir = Path("output")  
  
    output_dir.mkdir(  
        exist_ok=True  
    )  
  
    filename = (  
        f"{application_name}_"  
        f"{instance}_"  
        f"autosys_jobs.csv"  
    )  
  
    output_file = (  
        output_dir / filename  
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
    ]  
  
    with open(  
        output_file,  
        "w",  
        newline="",  
        encoding="utf-8"  
    ) as file:  
  
        writer = csv.DictWriter(  
            file,  
            fieldnames=columns  
        )  
  
        writer.writeheader()  
  
        writer.writerows(  
            jobs  
        )  
  
    return output_file  
  
  
# ---------------------------------------------------------  
# Main  
# ---------------------------------------------------------  
  
def main():  
  
    parser = argparse.ArgumentParser(  
        description=(  
            "Pull every AutoSys job belonging "  
            "to an application."  
        )  
    )  
  
    parser.add_argument(  
        "--application",  
        required=True,  
        help="AutoSys application attribute"  
    )  
  
    parser.add_argument(  
        "--instance",  
        required=True,  
        help="AutoSys instance such as PB3"  
    )  
  
    parser.add_argument(  
        "--no-ssl-verify",  
        action="store_true",  
        help="Disable SSL validation for local testing only"  
    )  
  
    args = parser.parse_args()  
  
    load_dotenv()  
  
    username = os.getenv(  
        "AUTOSYS_API_USER"  
    )  
  
    access_key = os.getenv(  
        "AUTOSYS_API_ACCESS_KEY"  
    )  
  
    if not username:  
        print(  
            "AUTOSYS_API_USER is missing."  
        )  
        return 1  
  
    if not access_key:  
        print(  
            "AUTOSYS_API_ACCESS_KEY is missing."  
        )  
        return 1  
  
    try:  
  
        instance = args.instance.upper()  
  
        jil_text = get_all_jil(  
            instance=instance,  
            username=username,  
            access_key=access_key,  
            verify_ssl=not args.no_ssl_verify  
        )  
  
        jobs = get_application_jobs(  
            jil_text=jil_text,  
            application_name=args.application,  
            instance=instance  
        )  
  
        print()  
        print(  
            f"Application : {args.application}"  
        )  
  
        print(  
            f"Instance    : {instance}"  
        )  
  
        print(  
            f"Jobs found  : {len(jobs)}"  
        )  
  
        print()  
  
        if not jobs:  
  
            print(  
                "No jobs found for the application."  
            )  
  
            return 2  
  
        for job in jobs:  
  
            print(  
                f"{job['job_name']:<55} "  
                f"{job['job_type'] or ''}"  
            )  
  
        output_file = write_csv(  
            application_name=args.application,  
            instance=instance,  
            jobs=jobs  
        )  
  
        print()  
        print(  
            f"CSV created: {output_file}"  
        )  
  
        return 0  
  
    except requests.HTTPError as exc:  
  
        print(  
            f"AutoSys API HTTP error: {exc}"  
        )  
  
        return 1  
  
    except requests.RequestException as exc:  
  
        print(  
            f"AutoSys connection error: {exc}"  
        )  
  
        return 1  
  
    except Exception as exc:  
  
        print(  
            f"Unexpected error: {exc}"  
        )  
  
        return 1  
  
  
if __name__ == "__main__":  
    sys.exit(main())  
