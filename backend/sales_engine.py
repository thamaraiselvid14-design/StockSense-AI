"""Sales Analytics Engine for StockSense AI.

Provides deterministic sales analytics calculations:
- Product sales performance & period-over-period growth %
- Best performing store identification
- Store sales comparison & top-two gap analysis
- Revenue trend & top product aggregations
- Category performance breakdown
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
    fetch_all,
    get_category_sales_performance,
    get_latest_sales_date,
    get_product_daily_sales_history,
    get_product_info,
    get_product_inventory,
    get_product_period_metrics,
    get_revenue_trend as db_get_revenue_trend,
    get_store_sales_comparison,
)
from backend.inventory_engine import (
    calculate_avg_daily_sales,
    calculate_days_remaining,
)


def get_product_performance(product_id, period_days=30):
    """Computes product sales performance, period-over-period revenue growth %, best performing store, and inventory metrics."""
    latest_date = get_latest_sales_date()
    if not latest_date:
        return {}

    ref_date = datetime.strptime(latest_date, "%Y-%m-%d")
    curr_start = (ref_date - timedelta(days=period_days - 1)).strftime("%Y-%m-%d")

    prev_end = (ref_date - timedelta(days=period_days)).strftime("%Y-%m-%d")
    prev_start = (ref_date - timedelta(days=period_days * 2 - 1)).strftime("%Y-%m-%d")

    info = get_product_info(product_id)
    curr_metrics = get_product_period_metrics(
        product_id, curr_start, latest_date
    )
    prev_metrics = get_product_period_metrics(product_id, prev_start, prev_end)

    curr_rev = curr_metrics["revenue"]
    prev_rev = prev_metrics["revenue"]

    if prev_rev == 0:
        growth_percent = None
    else:
        growth_percent = ((curr_rev - prev_rev) / prev_rev) * 100.0

    store_comp = get_store_sales_comparison(product_id, curr_start, latest_date)
    if store_comp and store_comp[0]["revenue"] > 0:
        best_performing_store = store_comp[0]
    else:
        best_performing_store = None

    current_stock = get_product_inventory(product_id)
    avg_sales = calculate_avg_daily_sales(
        product_id, store_id=None, window_days=7
    )
    days_rem = calculate_days_remaining(current_stock, avg_sales)

    return {
        "product_id": product_id,
        "product_name": info["product_name"] if info else product_id,
        "category": info["category"] if info else "",
        "price": info["price"] if info else 0.0,
        "reorder_level": info["reorder_level"] if info else 0,
        "period_days": period_days,
        "total_units_sold": curr_metrics["units_sold"],
        "total_revenue": curr_rev,
        "previous_period_units": prev_metrics["units_sold"],
        "previous_period_revenue": prev_rev,
        "growth_percent": growth_percent,
        "best_performing_store": best_performing_store,
        "current_stock": current_stock,
        "days_remaining": days_rem,
    }


def compare_stores(product_id, period_days=30):
    """Compares product sales across all 3 stores for the latest period_days and calculates gap between top two."""
    latest_date = get_latest_sales_date()
    if not latest_date:
        return {"stores": [], "gap_between_top_two": None}

    ref_date = datetime.strptime(latest_date, "%Y-%m-%d")
    start_date = (ref_date - timedelta(days=period_days - 1)).strftime("%Y-%m-%d")

    store_comp = get_store_sales_comparison(product_id, start_date, latest_date)

    if len(store_comp) >= 2:
        gap_between_top_two = (
            store_comp[0]["units_sold"] - store_comp[1]["units_sold"]
        )
    else:
        gap_between_top_two = None

    return {
        "stores": store_comp,
        "gap_between_top_two": gap_between_top_two,
        "df": pd.DataFrame(store_comp),
    }


def get_revenue_trend(days=30, store_id=None):
    """Delegates to database helper for daily revenue trend."""
    return db_get_revenue_trend(days=days, store_id=store_id)


def get_top_products(n=10, by="revenue", period_days=30):
    """Returns top N products aggregated over latest period_days by 'revenue' or 'units'."""
    latest_date = get_latest_sales_date()
    if not latest_date:
        return []

    order_col = "total_revenue" if by == "revenue" else "total_units"

    rows = fetch_all(
        f"""
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            SUM(s.revenue) as total_revenue,
            SUM(s.quantity) as total_units
        FROM Sales s
        JOIN Products p ON s.product_id = p.product_id
        WHERE s.date IN (
            SELECT DISTINCT date FROM Sales WHERE date <= ? ORDER BY date DESC LIMIT ?
        )
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY {order_col} DESC
        LIMIT ?
        """,
        (latest_date, period_days, n),
    )

    return [
        {
            "product_id": row["product_id"],
            "product": row["product_name"],
            "product_name": row["product_name"],
            "category": row["category"],
            "total_revenue": float(row["total_revenue"]),
            "total_units": int(row["total_units"]),
            "revenue": float(row["revenue"]),
            "units_sold": int(row["total_units"]),
        }
        for row in rows
    ]


def get_category_performance(period_days=30):
    """Returns category sales breakdown over the latest period_days."""
    latest_date = get_latest_sales_date()
    if not latest_date:
        return []

    ref_date = datetime.strptime(latest_date, "%Y-%m-%d")
    start_date = (ref_date - timedelta(days=period_days - 1)).strftime("%Y-%m-%d")

    return get_category_sales_performance(start_date, latest_date)
