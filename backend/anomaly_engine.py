"""Sales Anomaly Detection Engine for StockSense AI.

Provides deterministic sales spike and drop detection comparing recent demand velocity
against an immediately preceding non-overlapping baseline period.
"""

from datetime import datetime, timedelta
import os
import sys
import pandas as pd

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import (
    get_all_products_list,
    get_latest_sales_date,
    get_product_info,
    get_product_sales_total,
)

DEFAULT_SPIKE_THRESHOLD = 50
DEFAULT_DROP_THRESHOLD = -40


def detect_sales_spike_or_drop(
    product_id,
    store_id=None,
    recent_window=7,
    baseline_window=21,
    threshold_spike=DEFAULT_SPIKE_THRESHOLD,
    threshold_drop=DEFAULT_DROP_THRESHOLD,
):
    """Detects sales spike or drop for a product comparing recent_window against baseline_window.

    Returns dict containing anomaly metrics and status (SPIKE, DROP, NORMAL, or INSUFFICIENT_BASELINE).
    """
    latest_date = get_latest_sales_date()
    info = get_product_info(product_id)
    product_name = info["product_name"] if info else product_id
    category = info["category"] if info else ""

    if not latest_date:
        return {
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "store_id": store_id,
            "recent_window": recent_window,
            "baseline_window": baseline_window,
            "recent_units": 0,
            "baseline_units": 0,
            "recent_avg": 0.0,
            "baseline_avg": 0.0,
            "percent_change": None,
            "status": "INSUFFICIENT_BASELINE",
        }

    ref_date = datetime.strptime(latest_date, "%Y-%m-%d")

    rec_end = latest_date
    rec_start = (ref_date - timedelta(days=recent_window - 1)).strftime("%Y-%m-%d")

    base_end = (ref_date - timedelta(days=recent_window)).strftime("%Y-%m-%d")
    base_start = (
        ref_date - timedelta(days=recent_window + baseline_window - 1)
    ).strftime("%Y-%m-%d")

    recent_units = get_product_sales_total(
        product_id, store_id=store_id, start_date=rec_start, end_date=rec_end
    )
    baseline_units = get_product_sales_total(
        product_id, store_id=store_id, start_date=base_start, end_date=base_end
    )

    recent_avg = recent_units / float(recent_window)
    baseline_avg = baseline_units / float(baseline_window)

    if baseline_avg == 0:
        percent_change = None
        status = "INSUFFICIENT_BASELINE"
    else:
        percent_change = ((recent_avg - baseline_avg) / baseline_avg) * 100.0
        if percent_change >= threshold_spike:
            status = "SPIKE"
        elif percent_change <= threshold_drop:
            status = "DROP"
        else:
            status = "NORMAL"

    return {
        "product_id": product_id,
        "product_name": product_name,
        "category": category,
        "store_id": store_id,
        "recent_window": recent_window,
        "baseline_window": baseline_window,
        "recent_units": recent_units,
        "baseline_units": baseline_units,
        "recent_avg": recent_avg,
        "baseline_avg": baseline_avg,
        "percent_change": percent_change,
        "status": status,
    }


def get_all_anomalies(
    threshold_spike=DEFAULT_SPIKE_THRESHOLD,
    threshold_drop=DEFAULT_DROP_THRESHOLD,
):
    """Scans all 30 products and returns a pandas DataFrame of detected SPIKE and DROP anomalies sorted by severity."""
    products = get_all_products_list()
    anomalies = []

    for p in products:
        p_id = p["product_id"]
        res = detect_sales_spike_or_drop(
            p_id,
            store_id=None,
            recent_window=7,
            baseline_window=21,
            threshold_spike=threshold_spike,
            threshold_drop=threshold_drop,
        )

        if res["status"] in ["SPIKE", "DROP"]:
            anomalies.append(
                {
                    "product_id": res["product_id"],
                    "product": res["product_name"],
                    "category": res["category"],
                    "recent_avg": res["recent_avg"],
                    "baseline_avg": res["baseline_avg"],
                    "percent_change": res["percent_change"],
                    "status": res["status"],
                }
            )

    if not anomalies:
        return pd.DataFrame(
            columns=[
                "product_id",
                "product",
                "category",
                "recent_avg",
                "baseline_avg",
                "percent_change",
                "status",
            ]
        )

    df_anom = pd.DataFrame(anomalies)
    # Sort by absolute percent change descending
    df_anom["abs_change"] = df_anom["percent_change"].abs()
    df_anom = df_anom.sort_values(by="abs_change", ascending=False).drop(
        columns=["abs_change"]
    )

    return df_anom
