"""Query Router for StockSense AI.

Routes natural-language intent data to deterministic backend engines and constructs
verified, evidence-backed payloads with canonical recommendations.
"""

import difflib
import os
import sys
import pandas as pd

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.anomaly_engine import detect_sales_spike_or_drop, get_all_anomalies
from backend.database import (
    get_all_products_list,
    get_dashboard_kpis,
    get_latest_sales_date,
    get_product_info,
    get_stores_list,
)
from backend.inventory_engine import (
    calculate_avg_daily_sales,
    calculate_days_remaining,
    classify_stockout_risk,
    get_inventory_report,
)
from backend.messages import (
    MSG_MISSING_SUPPLIER_DATA,
    MSG_NO_RECENT_SALES,
    MSG_OUT_OF_DOMAIN,
    MSG_ZERO_INVENTORY,
    format_unknown_product_message,
)
from backend.recommendation_engine import recommend_action
from backend.sales_engine import compare_stores, get_product_performance


def resolve_product_id(product_query: str) -> str:
    """Resolves a product search string or ID to a valid product_id in Products table using 5-stage resolver.

    Stages:
    1. Case-insensitive exact match in Products table
    2. Normalized exact match (stripping punctuation/spaces)
    3. Unique contains / substring match
    4. High-confidence difflib typo match (cutoff >= 0.80)
    5. Otherwise return None (fail closed)
    """
    if not product_query:
        return None

    pq = str(product_query).strip()
    pq_lower = pq.lower()

    if pq_lower in ["null", "none", "all", "the product", "product", "a product", "this product", "any product"]:
        return None

    products = get_all_products_list()

    # Stage 1: Case-insensitive exact match on product_id or product_name
    for p in products:
        if p["product_id"].lower() == pq_lower or p["product_name"].lower() == pq_lower:
            return p["product_id"]

    # Stage 2: Normalized exact match (alphanumeric only)
    norm_pq = "".join(c for c in pq_lower if c.isalnum())
    for p in products:
        norm_name = "".join(c for c in p["product_name"].lower() if c.isalnum())
        norm_id = "".join(c for c in p["product_id"].lower() if c.isalnum())
        if norm_pq and (norm_pq == norm_name or norm_pq == norm_id):
            return p["product_id"]

    # Stage 3: Unique contains / substring match
    contains_matches = []
    for p in products:
        p_name = p["product_name"].lower()
        p_id = p["product_id"].lower()
        if pq_lower in p_name or pq_lower in p_id or p_name.startswith(pq_lower):
            contains_matches.append(p)

    if len(contains_matches) == 1:
        return contains_matches[0]["product_id"]
    elif len(contains_matches) > 1:
        # If multiple contain matches (e.g. "Pen"), pick match with exact word
        for cm in contains_matches:
            words = cm["product_name"].lower().split()
            if pq_lower in words:
                return cm["product_id"]
        return contains_matches[0]["product_id"]

    # Stage 4: High-confidence typo match using difflib (cutoff >= 0.80)
    candidates = {}
    for p in products:
        p_name_lower = p["product_name"].lower()
        candidates[p_name_lower] = p["product_id"]
        first_word = p_name_lower.split()[0]
        if first_word not in candidates:
            candidates[first_word] = p["product_id"]

    matches = difflib.get_close_matches(pq_lower, candidates.keys(), n=2, cutoff=0.80)
    if len(matches) == 1:
        return candidates[matches[0]]
    elif len(matches) > 1:
        ratio1 = difflib.SequenceMatcher(None, pq_lower, matches[0]).ratio()
        ratio2 = difflib.SequenceMatcher(None, pq_lower, matches[1]).ratio()
        if ratio1 >= 0.80 and (ratio1 - ratio2) >= 0.05:
            return candidates[matches[0]]

    # Stage 5: Fail closed -> No match
    return None


def resolve_store_id(store_query: str) -> str:
    """Resolves a store search string or ID to a valid store_id or None if all stores."""
    if not store_query or str(store_query).strip().lower() in ["all", "none", "null"]:
        return None

    sq = str(store_query).strip().lower()
    stores = get_stores_list()

    for s in stores:
        if s["store_id"].lower() == sq or sq in s["store_name"].lower() or sq in s["location"].lower():
            return s["store_id"]

    return None


def route_query(intent_data: dict) -> dict:
    """Executes deterministic Python queries based on intent_data and returns evidence payload."""
    if not isinstance(intent_data, dict):
        intent_data = {"intent": "unsupported"}

    intent = intent_data.get("intent", "unsupported")
    prod_query = intent_data.get("product")
    store_query = intent_data.get("store")
    unsupported_attr = intent_data.get("unsupported_attribute")

    store_id = resolve_store_id(store_query)

    # Edge Case 5: Missing Schema Attribute (e.g. Supplier of Milk)
    if unsupported_attr == "supplier" or (intent == "unsupported" and prod_query and any(w in str(prod_query).lower() for w in ["supplier", "vendor"])):
        resolved_pid = resolve_product_id(prod_query) if prod_query else None
        p_info = get_product_info(resolved_pid) if resolved_pid else None
        prod_display = p_info["product_name"] if p_info else (prod_query or "Product")

        f_text = MSG_MISSING_SUPPLIER_DATA
        a_text = "The current schema contains retail sales, products, stores, and inventory data but no supplier pricing information."
        ev_dict = {
            "recognized_product": prod_display,
            "missing_attribute": "supplier",
            "count": 0,
            "details": [],
        }

        return {
            "status": "unsupported",
            "intent": "unsupported",
            "finding": f_text,
            "summary": f_text,
            "recommendation": "No recommendation available",
            "recommended_action": "No recommendation available",
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": ev_dict,
            "details": [],
        }

    # Edge Case 4: Completely Out-of-Domain Question (e.g. Cricket)
    if intent == "unsupported":
        f_text = MSG_OUT_OF_DOMAIN
        a_text = "Only retail sales, inventory stock levels, and store performance are supported."
        return {
            "status": "unsupported",
            "intent": "unsupported",
            "finding": f_text,
            "summary": f_text,
            "recommendation": "No recommendation available",
            "recommended_action": "No recommendation available",
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": {"count": 0, "details": []},
            "details": [],
        }

    # Edge Case 3: Unknown Product (e.g. "iPhone") or Insufficient Data
    if intent == "insufficient_data":
        target_pid = resolve_product_id(prod_query) if prod_query else None
        if prod_query and not target_pid:
            f_text = format_unknown_product_message(prod_query)
        else:
            f_text = "Product name was missing or unspecified in your question."
        a_text = "Query requires a valid product name from the 30-item catalog."
        return {
            "status": "insufficient_data",
            "intent": "insufficient_data",
            "finding": f_text,
            "summary": f_text,
            "recommendation": "No recommendation available",
            "recommended_action": "No recommendation available",
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": {"count": 0, "details": []},
            "details": [],
        }

    # 1. Stockout Analysis
    if intent == "stockout_analysis":
        report_df = get_inventory_report(store_id=store_id)
        if prod_query:
            target_pid = resolve_product_id(prod_query)
            if target_pid:
                report_df = report_df[report_df["product_id"] == target_pid]
            else:
                f_text = format_unknown_product_message(prod_query)
                return {
                    "status": "insufficient_data",
                    "intent": "insufficient_data",
                    "finding": f_text,
                    "summary": f_text,
                    "recommendation": "No recommendation available",
                    "recommended_action": "No recommendation available",
                    "assumption": "Query requires a valid product name from catalog.",
                    "assumptions": "Query requires a valid product name from catalog.",
                    "evidence": {"count": 0, "details": []},
                    "details": [],
                }

        risk_df = report_df[report_df["stockout_risk"].isin(["OUT_OF_STOCK", "CRITICAL", "HIGH"])]

        items = []
        for _, r in risk_df.iterrows():
            days_rem = r["days_remaining"]
            items.append({
                "product_id": r["product_id"],
                "product": r["product"],
                "store": r["store"],
                "current_stock": int(r["current_stock"]),
                "days_remaining": round(days_rem, 1) if days_rem is not None else None,
                "stockout_risk": r["stockout_risk"],
                "note": MSG_ZERO_INVENTORY if int(r["current_stock"]) == 0 else None,
            })

        worst_risk = "SAFE"
        if any(i["stockout_risk"] == "OUT_OF_STOCK" for i in items):
            worst_risk = "OUT_OF_STOCK"
        elif any(i["stockout_risk"] == "CRITICAL" for i in items):
            worst_risk = "CRITICAL"
        elif any(i["stockout_risk"] == "HIGH" for i in items):
            worst_risk = "HIGH"

        rec = recommend_action({"stockout_risk": worst_risk})
        f_text = f"Identified {len(items)} product positions at elevated stock-out risk."
        a_text = "Calculations based on 7-day daily sales velocity and current store inventory balances."

        return {
            "status": "ok",
            "intent": intent,
            "finding": f_text,
            "summary": f_text,
            "recommendation": rec,
            "recommended_action": rec,
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": {"count": len(items), "details": items},
            "risk_count": len(items),
            "details": items,
        }

    # 2. Overstock Analysis
    elif intent == "overstock_analysis":
        report_df = get_inventory_report(store_id=store_id)
        if prod_query:
            target_pid = resolve_product_id(prod_query)
            if target_pid:
                report_df = report_df[report_df["product_id"] == target_pid]
            else:
                f_text = format_unknown_product_message(prod_query)
                return {
                    "status": "insufficient_data",
                    "intent": "insufficient_data",
                    "finding": f_text,
                    "summary": f_text,
                    "recommendation": "No recommendation available",
                    "recommended_action": "No recommendation available",
                    "assumption": "Query requires a valid product name from catalog.",
                    "assumptions": "Query requires a valid product name from catalog.",
                    "evidence": {"count": 0, "details": []},
                    "details": [],
                }

        overstock_df = report_df[report_df["overstock_flag"] == "OVERSTOCK_RISK"]

        items = []
        for _, r in overstock_df.iterrows():
            days_rem = r["days_remaining"]
            items.append({
                "product_id": r["product_id"],
                "product": r["product"],
                "store": r["store"],
                "current_stock": int(r["current_stock"]),
                "days_remaining": round(days_rem, 1) if days_rem is not None else None,
                "overstock_flag": r["overstock_flag"],
            })

        rec = recommend_action({"overstock_flag": "OVERSTOCK_RISK" if items else "NORMAL"})
        f_text = f"Identified {len(items)} overstocked inventory positions (>30 days supply)."
        a_text = "Overstock threshold set to 30 days of inventory supply based on 7-day average daily sales."

        return {
            "status": "ok",
            "intent": intent,
            "finding": f_text,
            "summary": f_text,
            "recommendation": rec,
            "recommended_action": rec,
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": {"count": len(items), "details": items},
            "overstock_count": len(items),
            "details": items,
        }

    # 3. Slow Moving Analysis
    elif intent == "slow_moving_analysis":
        report_df = get_inventory_report(store_id=store_id)
        if prod_query:
            target_pid = resolve_product_id(prod_query)
            if target_pid:
                report_df = report_df[report_df["product_id"] == target_pid]
            else:
                f_text = format_unknown_product_message(prod_query)
                return {
                    "status": "insufficient_data",
                    "intent": "insufficient_data",
                    "finding": f_text,
                    "summary": f_text,
                    "recommendation": "No recommendation available",
                    "recommended_action": "No recommendation available",
                    "assumption": "Query requires a valid product name from catalog.",
                    "assumptions": "Query requires a valid product name from catalog.",
                    "evidence": {"count": 0, "details": []},
                    "details": [],
                }

        slow_df = report_df[report_df["movement_status"].isin(["SLOW_MOVING", "NON_MOVING"])]

        items = []
        for _, r in slow_df.iterrows():
            items.append({
                "product_id": r["product_id"],
                "product": r["product"],
                "store": r["store"],
                "current_stock": int(r["current_stock"]),
                "movement_status": r["movement_status"],
                "note": MSG_NO_RECENT_SALES if r["avg_daily_sales"] is None else None,
            })

        worst_movement = "NON_MOVING" if any(i["movement_status"] == "NON_MOVING" for i in items) else ("SLOW_MOVING" if items else "NORMAL")
        rec = recommend_action({"movement_status": worst_movement})
        f_text = f"Identified {len(items)} slow-moving or non-moving inventory positions."
        a_text = "Slow-moving defined as recent 7-day velocity below 30% of prior 7-day velocity; non-moving defined as 0 sales in 14 days."

        return {
            "status": "ok",
            "intent": intent,
            "finding": f_text,
            "summary": f_text,
            "recommendation": rec,
            "recommended_action": rec,
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": {"count": len(items), "details": items},
            "slow_moving_count": len(items),
            "details": items,
        }

    # 4. Sales Anomaly
    elif intent == "sales_anomaly":
        if prod_query:
            target_pid = resolve_product_id(prod_query)
            if not target_pid:
                f_text = format_unknown_product_message(prod_query)
                a_text = "Sales anomaly check requires a valid product name from catalog."
                return {
                    "status": "insufficient_data",
                    "intent": "insufficient_data",
                    "finding": f_text,
                    "summary": f_text,
                    "recommendation": "No recommendation available",
                    "recommended_action": "No recommendation available",
                    "assumption": a_text,
                    "assumptions": a_text,
                    "evidence": {"count": 0, "details": []},
                    "details": [],
                }
            anom = detect_sales_spike_or_drop(target_pid, store_id=store_id)
            items = []
            if anom["status"] in ["SPIKE", "DROP"]:
                items.append({
                    "product_id": anom["product_id"],
                    "product": anom["product_name"],
                    "status": anom["status"],
                    "recent_avg": round(anom["recent_avg"], 2),
                    "baseline_avg": round(anom["baseline_avg"], 2),
                    "percent_change": round(anom["percent_change"], 1) if anom["percent_change"] else None,
                })
            rec = recommend_action({"anomaly_status": anom["status"]})
            f_text = f"Sales anomaly status for {anom['product_name']}: {anom['status']}."
            a_text = "Spikes defined as >=+50% change and drops as <=-40% change versus 21-day baseline."

            return {
                "status": "ok",
                "intent": intent,
                "finding": f_text,
                "summary": f_text,
                "recommendation": rec,
                "recommended_action": rec,
                "assumption": a_text,
                "assumptions": a_text,
                "evidence": {"count": len(items), "details": items},
                "anomaly_count": len(items),
                "details": items,
            }
        else:
            anom_df = get_all_anomalies()
            items = []
            for _, r in anom_df.iterrows():
                pct = r["percent_change"]
                items.append({
                    "product_id": r["product_id"],
                    "product": r["product"],
                    "status": r["status"],
                    "recent_avg": round(r["recent_avg"], 2),
                    "baseline_avg": round(r["baseline_avg"], 2),
                    "percent_change": round(pct, 1) if pct is not None else None,
                })

            has_spike = any(i["status"] == "SPIKE" for i in items)
            has_drop = any(i["status"] == "DROP" for i in items)
            rec_status = "SPIKE" if has_spike else ("DROP" if has_drop else "NORMAL")
            rec = recommend_action({"anomaly_status": rec_status})
            f_text = f"Detected {len(items)} sales anomalies (spikes/drops) across catalog."
            a_text = "Spikes defined as >=+50% change and drops as <=-40% change versus 21-day baseline."

            return {
                "status": "ok",
                "intent": intent,
                "finding": f_text,
                "summary": f_text,
                "recommendation": rec,
                "recommended_action": rec,
                "assumption": a_text,
                "assumptions": a_text,
                "evidence": {"count": len(items), "details": items},
                "anomaly_count": len(items),
                "details": items,
            }

    # 5. Product Performance
    elif intent == "product_performance":
        if not prod_query:
            f_text = "Please specify a product name to analyze sales performance."
            a_text = "Product performance analysis requires a specific product name from the catalog."
            return {
                "status": "insufficient_data",
                "intent": "insufficient_data",
                "finding": f_text,
                "summary": f_text,
                "recommendation": "No recommendation available",
                "recommended_action": "No recommendation available",
                "assumption": a_text,
                "assumptions": a_text,
                "evidence": {"count": 0, "details": []},
                "details": [],
            }

        target_pid = resolve_product_id(prod_query)
        if not target_pid:
            f_text = format_unknown_product_message(prod_query)
            a_text = "Product performance analysis requires a valid product from the 30-item catalog."
            return {
                "status": "insufficient_data",
                "intent": "insufficient_data",
                "finding": f_text,
                "summary": f_text,
                "recommendation": "No recommendation available",
                "recommended_action": "No recommendation available",
                "assumption": a_text,
                "assumptions": a_text,
                "evidence": {"count": 0, "details": []},
                "details": [],
            }

        perf = get_product_performance(target_pid, period_days=30)
        anom = detect_sales_spike_or_drop(target_pid)

        inv_df = get_inventory_report(store_id=store_id)
        p_inv = inv_df[inv_df["product_id"] == target_pid]

        if not p_inv.empty:
            avg_daily = calculate_avg_daily_sales(target_pid, store_id=store_id)
            days_rem = calculate_days_remaining(p_inv["current_stock"].sum(), avg_daily)
            stock_risk = classify_stockout_risk(days_rem)
            overstock = p_inv["overstock_flag"].iloc[0]
            movement = p_inv["movement_status"].iloc[0]
        else:
            days_rem = perf.get("days_remaining")
            stock_risk = "SAFE"
            overstock = "NORMAL"
            movement = "NORMAL"
            avg_daily = None

        # Pass retrieved signals through canonical recommend_action
        rec = recommend_action({
            "stockout_risk": stock_risk,
            "overstock_flag": overstock,
            "movement_status": movement,
            "anomaly_status": anom.get("status"),
            "days_remaining": days_rem,
            "current_stock": perf.get("current_stock"),
        })

        best_store_name = perf["best_performing_store"]["store_name"] if perf.get("best_performing_store") else "N/A"
        growth_pct = round(perf["growth_percent"], 1) if perf.get("growth_percent") is not None else None

        is_no_sales = pd.isna(avg_daily) or avg_daily is None
        f_text = f"30-day performance overview for {perf.get('product_name')}."
        if is_no_sales and perf.get("current_stock", 0) > 0:
            f_text += f" {MSG_NO_RECENT_SALES}"
        elif perf.get("current_stock", 0) == 0:
            f_text += f" {MSG_ZERO_INVENTORY}"

        a_text = "Metrics calculated over the latest 30-day period compared to prior 30 days."

        detail_items = [
            {
                "product_id": target_pid,
                "product": perf.get("product_name"),
                "category": perf.get("category"),
                "price": perf.get("price"),
                "30d_units_sold": perf.get("total_units_sold"),
                "30d_revenue": round(perf.get("total_revenue", 0.0), 2),
                "growth_percent": growth_pct,
                "best_store": best_store_name,
                "current_stock": perf.get("current_stock"),
                "days_remaining": round(days_rem, 1) if days_rem is not None else None,
                "stockout_risk": stock_risk,
                "anomaly_status": anom.get("status"),
                "note": MSG_NO_RECENT_SALES if is_no_sales else (MSG_ZERO_INVENTORY if perf.get("current_stock", 0) == 0 else None),
            }
        ]

        return {
            "status": "ok",
            "intent": intent,
            "finding": f_text,
            "summary": f_text,
            "recommendation": rec,
            "recommended_action": rec,
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": {"count": 1, "details": detail_items},
            "details": detail_items,
        }

    # 6. Store Comparison
    elif intent == "store_comparison":
        if not prod_query:
            f_text = "Please specify a product name to compare store performance."
            a_text = "Store comparison requires a specific product name from catalog."
            return {
                "status": "insufficient_data",
                "intent": "insufficient_data",
                "finding": f_text,
                "summary": f_text,
                "recommendation": "No recommendation available",
                "recommended_action": "No recommendation available",
                "assumption": a_text,
                "assumptions": a_text,
                "evidence": {"count": 0, "details": []},
                "details": [],
            }

        target_pid = resolve_product_id(prod_query)
        if not target_pid:
            f_text = format_unknown_product_message(prod_query)
            a_text = "Store comparison requires a valid product from the 30-item catalog."
            return {
                "status": "insufficient_data",
                "intent": "insufficient_data",
                "finding": f_text,
                "summary": f_text,
                "recommendation": "No recommendation available",
                "recommended_action": "No recommendation available",
                "assumption": a_text,
                "assumptions": a_text,
                "evidence": {"count": 0, "details": []},
                "details": [],
            }

        comp = compare_stores(target_pid, period_days=30)
        stores_data = comp.get("stores", [])

        items = []
        for s in stores_data:
            items.append({
                "store_id": s["store_id"],
                "store": s["store_name"],
                "location": s["location"],
                "units_sold": s["units_sold"],
                "revenue": round(s["revenue"], 2),
            })

        top_store = stores_data[0]["store_name"] if stores_data else "N/A"
        gap = comp.get("gap_between_top_two")

        rec = recommend_action({"stockout_risk": "SAFE"})
        f_text = f"Store sales comparison for {stores_data[0]['store_name'] if stores_data else target_pid} over 30 days."
        a_text = "30-day aggregated store sales comparison."

        return {
            "status": "ok",
            "intent": intent,
            "finding": f_text,
            "summary": f_text,
            "recommendation": rec,
            "recommended_action": rec,
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": {"count": len(items), "details": items, "top_performing_store": top_store, "lead_gap_units": gap},
            "top_performing_store": top_store,
            "lead_gap_units": gap,
            "details": items,
        }

    # 7. General Today Summary — EXACT KPI MATCH WITH DASHBOARD
    elif intent == "general_today_summary":
        kpis = get_dashboard_kpis()
        inv_df = get_inventory_report()
        anom_df = get_all_anomalies()

        stockout_cnt = len(inv_df[inv_df["stockout_risk"].isin(["OUT_OF_STOCK", "CRITICAL", "HIGH"])]) if not inv_df.empty else kpis.get("low_stock_count", 0)
        overstock_cnt = len(inv_df[inv_df["overstock_flag"] == "OVERSTOCK_RISK"]) if not inv_df.empty else 0
        slow_cnt = len(inv_df[inv_df["movement_status"].isin(["SLOW_MOVING", "NON_MOVING"])]) if not inv_df.empty else 0
        anom_cnt = len(anom_df) if not anom_df.empty else 0

        rec = recommend_action({
            "stockout_risk": "CRITICAL" if stockout_cnt > 0 else "SAFE",
            "overstock_flag": "OVERSTOCK_RISK" if overstock_cnt > 0 else "NORMAL",
        })

        f_text = f"Executive summary for retail operations on {kpis.get('latest_date')}: Today's Revenue ₹{kpis.get('todays_revenue', 0.0):,.2f}, Today's Units Sold {kpis.get('todays_units', 0):,}."
        a_text = f"Daily summary metrics for latest date {kpis.get('latest_date')} in SQLite database."

        ev_dict = {
            "latest_date": kpis.get("latest_date"),
            "todays_revenue": kpis.get("todays_revenue", 0.0),
            "todays_units": kpis.get("todays_units", 0),
            "stockout_risk_count": stockout_cnt,
            "overstock_count": overstock_cnt,
            "slow_moving_count": slow_cnt,
            "anomaly_count": anom_cnt,
        }

        return {
            "status": "ok",
            "intent": intent,
            "finding": f_text,
            "summary": f_text,
            "recommendation": rec,
            "recommended_action": rec,
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": ev_dict,
            "latest_date": kpis.get("latest_date"),
            "todays_revenue": kpis.get("todays_revenue", 0.0),
            "todays_units": kpis.get("todays_units", 0),
            "stockout_risk_count": stockout_cnt,
            "overstock_count": overstock_cnt,
            "slow_moving_count": slow_cnt,
            "anomaly_count": anom_cnt,
        }

    # Fallback -> No recommendation available
    else:
        f_text = MSG_OUT_OF_DOMAIN
        a_text = "Only retail sales, inventory stock levels, and store performance are supported."
        return {
            "status": "unsupported",
            "intent": "unsupported",
            "finding": f_text,
            "summary": f_text,
            "recommendation": "No recommendation available",
            "recommended_action": "No recommendation available",
            "assumption": a_text,
            "assumptions": a_text,
            "evidence": {"count": 0, "details": []},
            "details": [],
        }
