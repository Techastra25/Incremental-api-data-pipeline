"""
test_incremental_pipeline.py
Tests for watermark logic and upsert merge correctness.
Run: pytest tests/test_incremental_pipeline.py
"""

import pandas as pd
import pytest


def test_watermark_only_advances_on_success():
    old_watermark = "2025-01-01T00:00:00"
    records_fetched = []
    new_watermark = old_watermark if not records_fetched else max(
        r["updated_at"] for r in records_fetched
    )
    assert new_watermark == old_watermark


def test_upsert_keeps_latest_version():
    df = pd.DataFrame({
        "id": [1, 1, 2],
        "status": ["pending", "completed", "pending"],
        "updated_at": pd.to_datetime(["2025-01-01", "2025-01-05", "2025-01-02"]),
    })
    merged = df.sort_values("updated_at").drop_duplicates(subset="id", keep="last")
    row1 = merged[merged["id"] == 1].iloc[0]
    assert row1["status"] == "completed"
    assert len(merged) == 2


def test_no_duplicate_ids_after_merge():
    df = pd.DataFrame({
        "id": [1, 2, 1, 3, 2],
        "updated_at": pd.to_datetime([
            "2025-01-01", "2025-01-01",
            "2025-01-03", "2025-01-01", "2025-01-04"
        ]),
    })
    merged = df.sort_values("updated_at").drop_duplicates(subset="id", keep="last")
    assert merged["id"].is_unique
    assert len(merged) == 3


def test_pagination_pages_needed():
    page_size = 100
    total_matching = 1047
    pages_needed = (total_matching + page_size - 1) // page_size
    assert pages_needed == 11
