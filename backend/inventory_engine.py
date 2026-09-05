"""Inventory Intelligence Engine for StockSense AI.

Provides deterministic calculations for:
- Average Daily Sales
- Days Remaining
- Stock-out Risk Classification (OUT_OF_STOCK, CRITICAL, HIGH, MEDIUM, SAFE, UNKNOWN)
- Overstock Risk Detection (OVERSTOCK_RISK, NORMAL)
- Movement Status Detection (NON_MOVING, SLOW_MOVING, NORMAL)
- Full Inventory Report and Evidence-based Alerts
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
    get_inventory_with_windowed_sales,
    get_latest_sales_date,
    get_product_inventory,
    get_product_sales_total,
)


def calculate_avg_daily_sales(product_id, store_id=None, window_days=7):
    """Calculates average daily sales for a product/store over the latest calendar window_days.

    Returns None if total sales quantity during the window is 0.
    """
    latest_date = get_latest_sales_date()
    if not latest_date:
        return None

    ref_date = datetime.strptime(latest_date, "%Y-%m-%d")
    start_date = (ref_date - timedelta(days=window_days - 1)).strftime("%Y-%m-%d")

    total_units = get_product_sales_total(
        product_id, store_id=store_id, start_date=start_date, end_date=latest_date
    )

    if total_units <= 0:
        return None

    return total_units / float(window_days)


def calculate_days_remaining(current_stock, avg_daily_sales):
    """Calculates days of inventory remaining.

    - Returns 0 if current_stock == 0.
    - Returns None if avg_daily_sales is None or 0.
    - Returns current_stock / avg_daily_sales otherwise.
    """
    if current_stock == 0:
        return 0

    if avg_daily_sales is None or avg_daily_sales == 0:
        return None

    return current_stock / float(avg_daily_sales)


def classify_stockout_risk(days_remaining):
    """Classifies stock-out risk based on days remaining.

    - None                 -> UNKNOWN
    - 0                    -> OUT_OF_STOCK
    - 0 < days <= 2        -> CRITICAL
    - 2 < days <= 5        -> HIGH
    - 5 < days <= 10       -> MEDIUM
    - days > 10            -> SAFE
    """
    if days_remaining is None:
        return "UNKNOWN"

    if days_remaining == 0:
        return "OUT_OF_STOCK"

    if 0 < days_remaining <= 2:
        return "CRITICAL"

    if 2 < days_remaining <= 5:
        return "HIGH"

    if 5 < days_remaining <= 10:
        return "MEDIUM"

    if days_remaining > 10:
        return "SAFE"

    return "UNKNOWN"


def detect_overstock(product_id, store_id=None, threshold_days=30):
    """Detects if a product inventory position is overstocked (> threshold_days supply).

    Returns OVERSTOCK_RISK or NORMAL.
    """
    current_stock = get_product_inventory(product_id, store_id=store_id)
    avg_sales = calculate_avg_daily_sales(
        product_id, store_id=store_id, window_days=7
    )
    days_rem = calculate_days_remaining(current_stock, avg_sales)

    if days_rem is not None and days_rem > threshold_days:
        return "OVERSTOCK_RISK"

    return "NORMAL"


def detect_slow_moving(product_id, store_id=None):
    """Detects movement status based on recent 14-day sales velocity.

    Returns NON_MOVING, SLOW_MOVING, or NORMAL.
    """
    latest_date = get_latest_sales_date()
    if not latest_date:
        return "NORMAL"

    ref_date = datetime.strptime(latest_date, "%Y-%m-%d")

    rec_start = (ref_date - timedelta(days=6)).strftime("%Y-%m-%d")
    rec_end = latest_date

    prior_end = (ref_date - timedelta(days=7)).strftime("%Y-%m-%d")
    prior_start = (ref_date - timedelta(days=13)).strftime("%Y-%m-%d")

    recent_7_units = get_product_sales_total(
        product_id, store_id=store_id, start_date=rec_start, end_date=rec_end
    )
    prior_7_units = get_product_sales_total(
        product_id, store_id=store_id, start_date=prior_start, end_date=prior_end
    )

    last_14_units = recent_7_units + prior_7_units

    if last_14_units == 0:
        return "NON_MOVING"

    recent_7_avg = recent_7_units / 7.0
    prior_7_avg = prior_7_units / 7.0

    if prior_7_avg > 0 and recent_7_avg < 0.30 * prior_7_avg:
        return "SLOW_MOVING"

    return "NORMAL"


from backend.recommendation_engine import recommend_action


def get_recommended_action(
    stockout_risk,
    overstock_flag,
    movement_status,
    anomaly_status=None,
    days_remaining=None,
    current_stock=None,
):
    """Maps inventory signals to actionable recommendations using canonical recommendation engine."""
    return recommend_action(
        {
            "stockout_risk": stockout_risk,
            "overstock_flag": overstock_flag,
            "movement_status": movement_status,
            "anomaly_status": anomaly_status,
            "days_remaining": days_remaining,
            "current_stock": current_stock,
        }
    )


def get_inventory_report(store_id=None):
    """Returns a full pandas DataFrame containing all inventory positions with calculated metrics."""
    data = get_inventory_with_windowed_sales(recent_days=7, prior_days=7)

    if store_id:
        data = [item for item in data if item["store_id"] == store_id]

    rows = []
    for item in data:
        stock = item["current_stock"]
        rec_units = item["recent_7_units"]
        prior_units = item["prior_7_units"]
        last_14 = item["last_14_units"]

        avg_daily = (rec_units / 7.0) if rec_units > 0 else None
        days_rem = calculate_days_remaining(stock, avg_daily)
        risk = classify_stockout_risk(days_rem)
        overstock = (
            "OVERSTOCK_RISK"
            if (days_rem is not None and days_rem > 30)
            else "NORMAL"
        )

        if last_14 == 0:
            movement = "NON_MOVING"
        else:
            rec_avg = rec_units / 7.0
            prior_avg = prior_units / 7.0
            if prior_avg > 0 and rec_avg < 0.30 * prior_avg:
                movement = "SLOW_MOVING"
            else:
                movement = "NORMAL"

        action = get_recommended_action(
            risk, overstock, movement, days_remaining=days_rem, current_stock=stock
        )

        rows.append(
            {
                "product_id": item["product_id"],
                "product": item["product_name"],
                "category": item["category"],
                "price": item["price"],
                "reorder_level": item["reorder_level"],
                "store_id": item["store_id"],
                "store": f"{item['store_name']} ({item['location']})",
                "store_name": item["store_name"],
                "location": item["location"],
                "current_stock": stock,
                "last_updated": item["last_updated"],
                "recent_7_units": rec_units,
                "prior_7_units": prior_units,
                "last_14_units": last_14,
                "avg_daily_sales": avg_daily,
                "days_remaining": days_rem,
                "stockout_risk": risk,
                "overstock_flag": overstock,
                "movement_status": movement,
                "recommended_action": action,
            }
        )

    return pd.DataFrame(rows)
