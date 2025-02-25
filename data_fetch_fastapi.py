from fastapi import FastAPI, BackgroundTasks
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from cassandra.cluster import Cluster
import json
import os
from datetime import datetime, timedelta, timezone
import uuid
import time

app = FastAPI()

CASSANDRA_HOSTS = ["10.10.1.27", "10.10.2.36", "10.10.1.28"]
# Connect to Cassandra cluster and keyspace
cluster = Cluster(CASSANDRA_HOSTS)
session = cluster.connect()
session.set_keyspace('threat_intelligence')

scheduler = BackgroundScheduler()
scheduler.start()

def fetch_new_cves(session):
    cve_counter = 0
    last_updated = get_last_timestamp(session)
    now = datetime.now(timezone.utc)

    # Format timestamps for API
    start_date_str = last_updated.strftime("%Y-%m-%dT%H:%M:%S.000")
    end_date_str = now.strftime("%Y-%m-%dT%H:%M:%S.000")

    # Query NVD API
    nvd_url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={start_date_str}&pubEndDate={end_date_str}&resultsPerPage=2000"
    cve_data = fetch_data_with_retry(nvd_url)
    for cve in cve_data:
        cve_counter += 1
        cve_id = cve["cve"]["id"]
        timestamp = datetime.fromisoformat(cve["cve"]["published"])
        lastmodified = datetime.fromisoformat(cve["cve"]["lastModified"])
        metrics = cve["cve"]["metrics"].get("cvssMetricV31", [])
        baseScore = metrics[0]["cvssData"]["baseScore"] if metrics else None
        severity = metrics[0]["cvssData"]["baseSeverity"] if metrics else None
        description = cve["cve"]["descriptions"][0]["value"]
        source = cve["cve"]["sourceIdentifier"]
        status = cve["cve"]["vulnStatus"]
        #print(f"CVE ID: {cve_id}, Timestamp: {timestamp}, Last Modified: {lastmodified}, Base Score: {baseScore}, Severity: {severity}, Description: {description}, Source: {source}, Status: {status})

        insert_cve(session, cve_id, timestamp, lastmodified, baseScore, severity, description, source, status)
    else:
        print(f"Failed to fetch data from NVD API:")
    print("{} New CVE:s have been fetched at {}".format(cve_counter, datetime.now(timezone.utc)))

def fetch_initial_data(session):

    cve_counter = 0
    now = datetime.now(timezone.utc)
    end_date_str = now.strftime("%Y-%m-%dT%H:%M:%S.000")

    nvd_url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate=2025-01-01T00:00:00.000&pubEndDate={end_date_str}&resultsPerPage=2000"
    cve_data = fetch_data_with_retry(nvd_url)
    for cve in cve_data:
        cve_counter += 1
        cve_id = cve["cve"]["id"]
        timestamp = cve["cve"]["published"]
        lastmodified = cve["cve"]["lastModified"]
        metrics = cve["cve"]["metrics"].get("cvssMetricV31", [])
        baseScore = metrics[0]["cvssData"]["baseScore"] if metrics else None
        severity = metrics[0]["cvssData"]["baseSeverity"] if metrics else None
        description = cve["cve"]["descriptions"][0]["value"]
        source = cve["cve"]["sourceIdentifier"]
        status = cve["cve"]["vulnStatus"]
        tags = cve["cve"]["cveTags"]
        insert_cve(session, cve_id, timestamp, lastmodified, baseScore, severity, description, source, status, tags)
        #print(f"CVE ID: {cve_id}, Timestamp: {timestamp}, Last Modified: {lastmodified}, Base Score: {baseScore}, Severity: {severity}, Description: {description}, Source: {source}, Status: {status}, Tags: {tags}")            #insert_cve(session, cve_id, timestamp, lastmodified, baseScore, severity, description, source, status, tags)
        last_modified_date = datetime.fromisoformat(timestamp).strftime("%Y-%m-%dT%H:%M:%S.000")

    else:
        print(f"Failed to fetch data from NVD API: {response.status_code}")
    print("CVE_counter: ", cve_counter)
    time.sleep(2)
    total_results = get_total_results()
    time.sleep(2)
    while True:
        time.sleep(2)
        nvd_url_updated = f"https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate={last_modified_date}&pubEndDate={end_date_str}&resultsPerPage=2000"
        response = requests.get(nvd_url_updated)
        if response.status_code == 200:
            cve_data = response.json().get("vulnerabilities", [])
            for cve in cve_data:
                if cve_counter == total_results:
                    break
                cve_counter += 1
                cve_id = cve["cve"]["id"]
                timestamp = cve["cve"]["published"]
                lastmodified = cve["cve"]["lastModified"]
                metrics = cve["cve"]["metrics"].get("cvssMetricV31", [])
                baseScore = metrics[0]["cvssData"]["baseScore"] if metrics else None
                severity = metrics[0]["cvssData"]["baseSeverity"] if metrics else None
                description = cve["cve"]["descriptions"][0]["value"]
                source = cve["cve"]["sourceIdentifier"]
                status = cve["cve"]["vulnStatus"]
                tags = cve["cve"]["cveTags"]
                #print(f"CVE ID: {cve_id}, Timestamp: {timestamp}, Last Modified: {lastmodified}, Base Score: {baseScore}, Severity: {severity}, Description: {description}, Source: {source}, Status: {status}, Tags: {tags}")
                print(cve_counter)
                #insert_cve(session, cve_id, timestamp, lastmodified, baseScore, severity, description, source, status, tags)
            last_modified_date = datetime.fromisoformat(timestamp).strftime("%Y-%m-%dT%H:%M:%S.000")
            print("CVE_counter: ", cve_counter)
            if cve_counter == total_results:
                break
        else:
            print(f"Failed to fetch data from NVD API: {response.status_code}")
    print("All cve:s have been fetched from the year 2025, there were {} cve found".format(cve_counter))

def fetch_data_with_retry(url, max_retries=5):
    retries = 0
    while retries < max_retries:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("vulnerabilities", [])
        elif response.status_code == 503:
            wait_time = 2 ** retries  # Exponential backoff
            print(f"NVD API returned 503, retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retries += 1
        else:
            response.raise_for_status()
    raise Exception("NVD API is unavailable after multiple retries.")

def get_total_results():
    total_results_url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?resultsPerPage=1&startIndex=0&pubStartDate=2025-01-01T00:00:00.000&pubEndDate=2025-02-12T00:00:00.000"
    response = requests.get(total_results_url)
    total_results = response.json().get("totalResults")
    return total_results


def get_last_timestamp(session):
    query = "SELECT MAX(lastmodified) FROM vulnerabilities"
    result = session.execute(query).one()
    return result[0] if result and result[0] else datetime.now(tz=datetime.timezone.utc) - timedelta(days=1)


def insert_cve(session, cve, timestamp, lastmodified, baseScore, severity, description, source, status, tags):
    cassandra_q = """
    INSERT INTO vulnerabilities (id, cve, timestamp, lastmodified, baseScore, severity, description, source, status, tags)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    session.execute(cassandra_q, (uuid.uuid4(), cve, timestamp, lastmodified, baseScore, severity, description, source, status, tags))

@app.get("/")
def root():
    return {"message": "Threat Intelligence API is running"}

@app.post("/fetch-latest")
def trigger_fetch_latest(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_new_cves)
    return {"message": "Fetching latest CVEs in the background"}

@app.post("/fetch-initial")
def trigger_fetch_initial(background_tasks: BackgroundTasks):
    # Check if Cassandra table is empty
    row_count = session.execute("SELECT COUNT(*) FROM vulnerabilities").one()[0]
    if row_count == 0:
        background_tasks.add_task(fetch_initial_data)
        return {"message": "Fetching initial CVEs since Cassandra was empty"}
    return {"message": "Cassandra already has data, skipping initial fetch"}

scheduler.add_job(fetch_new_cves, 'interval', hours=1, args=[session])

nvd_api_url = "https://services.nvd.nist.gov/rest/json/cves/2.0/?resultsPerPage=1&startIndex=3000&pubStartDate=2025-01-01T00:00:00.000&pubEndDate=2025-02-12T00:00:00.000"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)