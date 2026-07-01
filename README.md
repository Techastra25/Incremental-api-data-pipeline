# Incremental API Data Pipeline

A REST API ingestion pipeline implementing the **watermark-based
incremental sync pattern** — the standard approach for pulling data
from any external SaaS/CRM/payments API (Stripe, Salesforce, HubSpot-style)
without re-fetching the entire dataset on every run.

## Why this exists

Most real-world data sources aren't files dropped in a folder — they're
APIs you have to poll, where a full re-pull is slow, expensive, and often
rate-limited. This pipeline solves that with a watermark: it tracks the
timestamp of the most recently synced record and only requests data
updated after that point on each subsequent run, then merges new/changed
records into a deduplicated current-state table.

## Architecture
External REST API (paginated, supports ?updated_since=<timestamp>)
│
▼  incremental_ingest.py
Watermark check (data/watermark.json)
│
▼  Paginated fetch of only NEW/changed records
Raw sync files (data/raw/orders_sync_<timestamp>.json)
│
▼  process_and_merge.py
Upsert merge: keep latest version per id, drop duplicates
│
▼
Current-state table (data/processed/orders_current_state.csv)
│
▼  (production: UPSERT into Postgres/Azure SQL via sql/create_orders_table.sql)

## Actual Run Results (Real Output)

Two incremental sync runs against 3,000 source records:

[Run 1] historical load up to 2025-04-01: fetched 1953 records, watermark -> 2025-03-31T22:45:00
[Run 2] incremental sync: fetched 1047 NEW records (not 3000 again)
Total source records: 3000 | Run1 + Run2 = 3000 (matches exactly)

After upsert merge:

[process] loaded 3000 raw records across 2 sync files
[process] upsert merge: 3000 raw rows -> 3000 unique current-state rows
[process] validation passed: no duplicate ids, no null order totals
Status breakdown:
refunded     785
cancelled    753
pending      733
completed    729
Total order value (current state): 2,987,710.31

## What makes this production-grade

- Watermark only advances after successful complete write
- Upsert semantics — only latest version of each record survives
- Pagination handled properly across all pages
- Validation after every merge catches data quality regressions
- 4 unit tests covering all correctness-critical logic

## Running locally

```bash
pip install -r requirements.txt

# Terminal 1
python src/ingestion/mock_api_server.py

# Terminal 2
python src/ingestion/incremental_ingest.py
python src/processing/process_and_merge.py
pytest tests/
```

## Repo structure
incremental-api-data-pipeline/
├── src/
│   ├── ingestion/
│   │   ├── mock_api_server.py
│   │   └── incremental_ingest.py
│   └── processing/
│       └── process_and_merge.py
├── sql/create_orders_table.sql
├── tests/test_incremental_pipeline.py
├── requirements.txt
└── .gitignore
