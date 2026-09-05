"""Comprehensive Edge-Case Regression Test Suite for StockSense AI.

Run via: python tests/test_edge_cases.py
"""

import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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
from backend.query_router import resolve_product_id, route_query
from backend.recommendation_engine import recommend_action
from backend.gemini_service import parse_json_safely, validate_numeric_safety, generate_grounded_explanation


import pandas as pd

def test_a_no_recent_sales():
    print("[TEST A] Checking product/store with stock > 0 and 0 recent sales...")
    report_df = get_inventory_report()
    no_sales_rows = report_df[(report_df["current_stock"] > 0) & (report_df["recent_7_units"] == 0)]
    
    assert not no_sales_rows.empty, "Database must contain at least one position with stock > 0 and 0 recent sales"
    
    sample_row = no_sales_rows.iloc[0]
    p_id = sample_row["product_id"]
    st_id = sample_row["store_id"]
    stock = sample_row["current_stock"]
    
    # Direct function test on backend engine
    calc_avg = calculate_avg_daily_sales(p_id, store_id=st_id)
    assert calc_avg is None, f"calculate_avg_daily_sales should return None, got {calc_avg}"
    
    avg_sales = sample_row["avg_daily_sales"]
    days_rem = sample_row["days_remaining"]
    risk = sample_row["stockout_risk"]
    
    assert pd.isna(avg_sales) or avg_sales is None, f"Expected avg_daily_sales is None/NaN for {p_id}, got {avg_sales}"
    assert pd.isna(days_rem) or days_rem is None, f"Expected days_remaining is None/NaN for {p_id}, got {days_rem}"
    assert risk == "UNKNOWN", f"Expected stockout_risk == UNKNOWN for {p_id}, got {risk}"
    
    # Check query_router payload includes MSG_NO_RECENT_SALES
    payload = route_query({"intent": "product_performance", "product": p_id, "store": st_id})
    details = payload.get("details", [])
    assert details, "Payload details should not be empty"
    note = details[0].get("note")
    assert note == MSG_NO_RECENT_SALES, f"Expected note '{MSG_NO_RECENT_SALES}', got '{note}'"
    print("  [OK] TEST A PASSED: No recent sales handled cleanly (N/A / N/A / UNKNOWN).")


def test_b_zero_inventory():
    print("[TEST B] Checking product/store with current_stock == 0...")
    report_df = get_inventory_report()
    zero_stock_rows = report_df[report_df["current_stock"] == 0]
    
    assert not zero_stock_rows.empty, "Database must contain at least one zero-stock position"
    
    sample_row = zero_stock_rows.iloc[0]
    p_id = sample_row["product_id"]
    days_rem = sample_row["days_remaining"]
    risk = sample_row["stockout_risk"]
    
    assert days_rem == 0 or days_rem == 0.0, f"Expected days_remaining == 0 for zero stock, got {days_rem}"
    assert risk == "OUT_OF_STOCK", f"Expected stockout_risk == OUT_OF_STOCK, got {risk}"
    
    rec = recommend_action({"stockout_risk": risk})
    assert rec == "Replenish immediately", f"Expected 'Replenish immediately', got '{rec}'"
    
    payload = route_query({"intent": "stockout_analysis", "product": p_id})
    items = payload.get("details", [])
    assert items, "Stockout analysis details should not be empty"
    note = items[0].get("note")
    assert note == MSG_ZERO_INVENTORY, f"Expected note '{MSG_ZERO_INVENTORY}', got '{note}'"
    print("  [OK] TEST B PASSED: Zero inventory correctly classified as OUT_OF_STOCK.")


def test_c_unknown_product():
    print("[TEST C] Checking unknown product handling ('iPhone')...")
    payload = route_query({"intent": "product_performance", "product": "iPhone", "store": None, "timeframe": None})
    
    assert payload.get("status") == "insufficient_data", f"Expected status == insufficient_data, got {payload.get('status')}"
    finding = payload.get("finding")
    expected_finding = format_unknown_product_message("iPhone")
    assert finding == expected_finding, f"Expected finding '{expected_finding}', got '{finding}'"
    rec = payload.get("recommendation")
    assert rec == "No recommendation available", f"Expected 'No recommendation available', got '{rec}'"
    print("  [OK] TEST C PASSED: Unknown product 'iPhone' failed closed gracefully.")


def test_d_out_of_domain():
    print("[TEST D] Checking completely out-of-domain question (Cricket)...")
    payload = route_query({"intent": "unsupported", "product": None})
    
    assert payload.get("status") == "unsupported", f"Expected status == unsupported, got {payload.get('status')}"
    finding = payload.get("finding")
    assert finding == MSG_OUT_OF_DOMAIN, f"Expected finding '{MSG_OUT_OF_DOMAIN}', got '{finding}'"
    rec = payload.get("recommendation")
    assert rec == "No recommendation available", f"Expected 'No recommendation available', got '{rec}'"
    print("  [OK] TEST D PASSED: Out-of-domain question handled with standard unsupported response.")


def test_e_missing_schema_attribute():
    print("[TEST E] Checking valid entity with missing schema attribute (Supplier of Milk)...")
    payload = route_query({
        "intent": "unsupported",
        "product": "Milk",
        "store": None,
        "timeframe": None,
        "unsupported_attribute": "supplier"
    })
    
    assert payload.get("status") == "unsupported", f"Expected status == unsupported, got {payload.get('status')}"
    finding = payload.get("finding")
    assert finding == MSG_MISSING_SUPPLIER_DATA, f"Expected finding '{MSG_MISSING_SUPPLIER_DATA}', got '{finding}'"
    
    ev = payload.get("evidence", {})
    assert ev.get("recognized_product") == "Milk 1L", f"Expected recognized_product == 'Milk 1L', got '{ev.get('recognized_product')}'"
    assert ev.get("missing_attribute") == "supplier", f"Expected missing_attribute == 'supplier', got '{ev.get('missing_attribute')}'"
    
    rec = payload.get("recommendation")
    assert rec == "No recommendation available", f"Expected 'No recommendation available', got '{rec}'"
    print("  [OK] TEST E PASSED: Missing supplier attribute handled with recognized product evidence.")


def test_f_gemini_failure_handling():
    print("[TEST F] Checking Gemini failure / malformed JSON safeguards...")
    parsed_bad = parse_json_safely("Not a JSON string at all")
    assert parsed_bad.get("intent") == "unsupported", "Malformed JSON should parse to unsupported intent"
    
    parsed_codeblock = parse_json_safely("```json\n{\"intent\": \"sales_anomaly\"}\n```")
    assert parsed_codeblock.get("intent") == "sales_anomaly", "Code block JSON should be extracted"
    
    # Grounded explanation fallback for unsupported
    p_unsupported = {"status": "unsupported", "finding": MSG_OUT_OF_DOMAIN, "recommendation": "No recommendation available"}
    exp = generate_grounded_explanation("Cricket match", {"intent": "unsupported"}, p_unsupported)
    assert MSG_OUT_OF_DOMAIN in exp, "Fallback explanation should contain MSG_OUT_OF_DOMAIN"
    
    # Numeric safety validation check
    safety = validate_numeric_safety("Revenue is 100", {"revenue": 100})
    assert safety["is_safe"] is True, "Matching number should pass numeric safety"
    safety_bad = validate_numeric_safety("Revenue is 999999", {"revenue": 100})
    assert safety_bad["is_safe"] is False, "Ungrounded number should trigger numeric safety flag"
    print("  [OK] TEST F PASSED: Gemini failure and defensive parsing safeguards verified.")


def test_g_fuzzy_matching():
    print("[TEST G] Checking 5-stage entity resolver fuzzy matching and fail-closed thresholds...")
    res_coffe = resolve_product_id("Coffe")
    assert res_coffe == "P006", f"Expected 'P006' for 'Coffe', got {res_coffe}"
    
    res_shampo = resolve_product_id("Shampo")
    assert res_shampo == "P012", f"Expected 'P012' for 'Shampo', got {res_shampo}"
    
    res_iphone = resolve_product_id("iPhone")
    assert res_iphone is None, f"Expected None for 'iPhone', got {res_iphone}"
    
    res_laptop = resolve_product_id("Laptop")
    assert res_laptop is None, f"Expected None for 'Laptop', got {res_laptop}"
    
    res_supplier = resolve_product_id("Supplier")
    assert res_supplier is None, f"Expected None for 'Supplier', got {res_supplier}"
    print("  [OK] TEST G PASSED: Fuzzy matching handles near-typos ('Coffe', 'Shampo') and fails closed on 'iPhone'/'Laptop'.")


if __name__ == "__main__":
    print("==========================================================")
    print("RUNNING STOCKSENSE AI PHASE 6 EDGE-CASE REGRESSION SUITE")
    print("==========================================================")
    
    test_a_no_recent_sales()
    test_b_zero_inventory()
    test_c_unknown_product()
    test_d_out_of_domain()
    test_e_missing_schema_attribute()
    test_f_gemini_failure_handling()
    test_g_fuzzy_matching()
    
    print("\n==========================================================")
    print("ALL PHASE 6 EDGE-CASE REGRESSION TESTS PASSED SUCCESSFULLY!")
    print("==========================================================")
