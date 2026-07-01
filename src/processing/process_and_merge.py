"""
process_and_merge.py
-----------------------
Merges incremental sync files into a deduplicated current-state table.
Implements upsert semantics: keep only the latest version per id.

Run: python src/processing/process_and_merge.py
"""

import glob
import json
import os
import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"


def load_all_raw_files():
    files = sorted(glob.glob(f"{RAW_DIR}/orders_sync_*.json"))
    if not files:
        raise FileNotFoundError("No sync files found. Run incremental_ingest.py first.")
    all_records = []
    for f in files:
        with open(f) as fh:
            all_records.extend(json.load(fh))
    print(f"[process] loaded {len(all_records)} raw records across {len(files)} sync files")
    return pd.DataFrame(all_records)


def upsert_merge(df: pd.DataFrame) -> pd.DataFrame:
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    before = len(df)
    merged = df.sort_values("updated_at").drop_duplicates(subset="id", keep="last").reset_index(drop=True)
    print(f"[process] upsert merge: {before} raw rows -> {len(merged)} unique current-state rows")
    return merged


def validate(df: pd.DataFrame):
    issues = []
    if df["id"].duplicated().any():
        issues.append("duplicate ids found after merge")
    if df["order_total"].isna().any():
        issues.append(f"{df['order_total'].isna().sum()} rows have null order_total")
    if not issues:
        print("[process] validation passed: no duplicate ids, no null order totals")
    else:
        for issue in issues:
            print(f"[process][WARNING] {issue}")
    return issues


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    df = load_all_raw_files()
    merged = upsert_merge(df)
    validate(merged)

    out_path = f"{PROCESSED_DIR}/orders_current_state.csv"
    merged.to_csv(out_path, index=False)
    print(f"[process] current-state table -> {out_path}")

    print("\nStatus breakdown:")
    print(merged["status"].value_counts().to_string())
    print(f"\nTotal order value: {merged['order_total'].sum():,.2f}")


if __name__ == "__main__":
    main()
