"""
incremental_ingest.py
-----------------------
Watermark-based incremental ingestion from a paginated REST API.
Only fetches records updated since the last successful run.

Run: python src/ingestion/incremental_ingest.py
"""

import json
import os
import time
import requests
import pandas as pd

API_BASE = "http://localhost:5050/api/orders"
WATERMARK_FILE = "data/watermark.json"
RAW_DIR = "data/raw"
PAGE_SIZE = 100


def get_watermark() -> str:
    if os.path.exists(WATERMARK_FILE):
        with open(WATERMARK_FILE) as f:
            return json.load(f)["last_updated_at"]
    return "2000-01-01T00:00:00"


def set_watermark(value: str):
    os.makedirs(os.path.dirname(WATERMARK_FILE), exist_ok=True)
    with open(WATERMARK_FILE, "w") as f:
        json.dump({
            "last_updated_at": value,
            "set_at": pd.Timestamp.now().isoformat()
        }, f)


def fetch_all_pages(updated_since: str):
    page = 1
    all_records = []
    while True:
        resp = requests.get(API_BASE, params={
            "updated_since": updated_since,
            "page": page,
            "page_size": PAGE_SIZE,
        }, timeout=10)
        resp.raise_for_status()
        body = resp.json()
        all_records.extend(body["data"])
        print(f"  page {page}: {len(body['data'])} records (total: {len(all_records)})")
        if not body["has_more"]:
            break
        page += 1
        time.sleep(0.05)
    return all_records


def run_incremental_sync():
    watermark = get_watermark()
    print(f"[sync] watermark = {watermark}")

    records = fetch_all_pages(watermark)

    if not records:
        print("[sync] no new records since last watermark.")
        return 0

    os.makedirs(RAW_DIR, exist_ok=True)
    run_ts = pd.Timestamp.now().strftime("%Y%m%dT%H%M%S")
    out_path = f"{RAW_DIR}/orders_sync_{run_ts}.json"
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)

    # CRITICAL: watermark advances ONLY after successful write
    new_watermark = max(r["updated_at"] for r in records)
    set_watermark(new_watermark)

    print(f"[sync] wrote {len(records)} records -> {out_path}")
    print(f"[sync] watermark advanced to {new_watermark}")
    return len(records)


if __name__ == "__main__":
    run_incremental_sync()
