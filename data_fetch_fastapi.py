from fastapi import FastAPI, BackgroundTasks
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from confluent_kafka import Producer
import json
from datetime import datetime, timedelta, timezone
import time

app = FastAPI()

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "cve_data"

producer = Producer({"bootstrap.servers": KAFKA_BROKER})

scheduler = BackgroundScheduler()
scheduler.start()


def fetch_new_cves():
    cve_counter = 0
    last_updated = get_last_timestamp()
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

        send_to_kafka(
            cve_id,
            timestamp,
            lastmodified,
            baseScore,
            severity,
            description,
            source,
            status,
        )
    else:
        print(f"Failed to fetch data from NVD API:")
    print(
        "{} New CVE:s have been fetched at {}".format(
            cve_counter, datetime.now(timezone.utc)
        )
    )


def fetch_initial_data():
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
        send_to_kafka(
            cve_id,
            timestamp,
            lastmodified,
            baseScore,
            severity,
            description,
            source,
            status,
            tags,
        )
        last_modified_date = datetime.fromisoformat(timestamp).strftime(
            "%Y-%m-%dT%H:%M:%S.000"
        )

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
                send_to_kafka(
                    cve_id,
                    timestamp,
                    lastmodified,
                    baseScore,
                    severity,
                    description,
                    source,
                    status,
                    tags,
                )
            last_modified_date = datetime.fromisoformat(timestamp).strftime(
                "%Y-%m-%dT%H:%M:%S.000"
            )
            print("CVE_counter: ", cve_counter)
            if cve_counter == total_results:
                break
        else:
            print(f"Failed to fetch data from NVD API: {response.status_code}")
    print(
        "All cve:s have been fetched from the year 2025, there were {} cve found".format(
            cve_counter
        )
    )


def fetch_data_with_retry(url, max_retries=5):
    retries = 0
    while retries < max_retries:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("vulnerabilities", [])
        elif response.status_code == 503:
            wait_time = 2**retries  # Exponential backoff
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


def get_last_timestamp():
    # This function should return the last timestamp from your Kafka topic or another source
    # For simplicity, we'll return the current time minus one day
    return datetime.now(timezone.utc) - timedelta(days=1)


def send_to_kafka(
    cve_id,
    timestamp,
    lastmodified,
    baseScore,
    severity,
    description,
    source,
    status,
    tags=None,
):
    cve_data = {
        "cve_id": cve_id,
        "timestamp": timestamp.isoformat(),
        "lastmodified": lastmodified.isoformat(),
        "baseScore": baseScore,
        "severity": severity,
        "description": description,
        "source": source,
        "status": status,
        "tags": tags,
    }
    producer.produce(KAFKA_TOPIC, key=cve_id, value=json.dumps(cve_data))
    producer.flush()


@app.get("/")
def root():
    return {"message": "Threat Intelligence API is running"}


@app.post("/fetch-latest")
def trigger_fetch_latest(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_new_cves)
    return {"message": "Fetching latest CVEs in the background"}


@app.post("/fetch-initial")
def trigger_fetch_initial(background_tasks: BackgroundTasks):
    # Check if Kafka topic is empty
    # For simplicity, we'll assume it's empty and always fetch initial data
    background_tasks.add_task(fetch_initial_data)
    return {"message": "Fetching initial CVEs"}


scheduler.add_job(fetch_new_cves, "interval", hours=1)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
