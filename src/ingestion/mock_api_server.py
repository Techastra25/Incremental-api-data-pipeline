"""
mock_api_server.py
--------------------
Simulates a real paginated REST API with incremental update support.
Replaces a real third-party API for local development/testing.

Run: python src/ingestion/mock_api_server.py
"""

import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

random.seed(42)
RECORDS = []
base_time = datetime(2025, 1, 1)
for i in range(1, 3001):
    updated = base_time + timedelta(minutes=random.randint(0, 200000))
    RECORDS.append({
        "id": i,
        "customer_name": f"Customer_{i}",
        "order_total": round(random.uniform(10, 2000), 2),
        "status": random.choice(["completed", "pending", "cancelled", "refunded"]),
        "updated_at": updated.isoformat(),
    })


@app.route("/api/orders", methods=["GET"])
def get_orders():
    updated_since = request.args.get("updated_since", "2000-01-01T00:00:00")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 100))

    cutoff = datetime.fromisoformat(updated_since)
    matching = [r for r in RECORDS if datetime.fromisoformat(r["updated_at"]) > cutoff]
    matching.sort(key=lambda r: r["updated_at"])

    start = (page - 1) * page_size
    end = start + page_size

    return jsonify({
        "data": matching[start:end],
        "page": page,
        "page_size": page_size,
        "total_matching": len(matching),
        "has_more": end < len(matching),
    })


if __name__ == "__main__":
    print(f"Mock API serving {len(RECORDS)} records on http://localhost:5050")
    app.run(port=5050, debug=False)
