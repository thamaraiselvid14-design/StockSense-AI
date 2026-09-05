"""Canonical Recommendation Engine for StockSense AI.

Maps calculated inventory metrics and sales anomaly signals into evidence-backed,
actionable manager recommendations using strict priority precedence.
"""


def recommend_action(context: dict) -> str:
    """Maps inventory and anomaly signals to a canonical recommendation string.

    Canonical precedence:
    1. OUT_OF_STOCK   -> "Replenish immediately"
    2. CRITICAL       -> "Replenish immediately"
    3. SPIKE + HIGH   -> "Increase replenishment priority"
    4. HIGH           -> "Reorder soon"
    5. OVERSTOCK_RISK -> "Reduce next order"
    6. DROP           -> "Investigate demand"
    7. NON_MOVING     -> "Investigate demand"
    8. SLOW_MOVING     -> "Investigate demand"
    9. MEDIUM         -> "Monitor stock closely"
    10. UNKNOWN       -> "Review demand history"
    11. default       -> "No action needed"
    """
    if not isinstance(context, dict):
        return "No action needed"

    stockout_risk = context.get("stockout_risk")
    overstock_flag = context.get("overstock_flag")
    movement_status = context.get("movement_status")
    anomaly_status = context.get("anomaly_status")
    days_remaining = context.get("days_remaining")

    # 1 & 2. OUT_OF_STOCK / CRITICAL
    if stockout_risk == "OUT_OF_STOCK":
        return "Replenish immediately"

    if stockout_risk == "CRITICAL":
        return "Replenish immediately"

    # 3. SPIKE + HIGH / CRITICAL
    if anomaly_status == "SPIKE" and (
        stockout_risk in ["CRITICAL", "HIGH"]
        or (days_remaining is not None and days_remaining <= 5)
    ):
        return "Increase replenishment priority"

    # 4. HIGH
    if stockout_risk == "HIGH":
        return "Reorder soon"

    # 5. OVERSTOCK_RISK
    if overstock_flag == "OVERSTOCK_RISK":
        return "Reduce next order"

    # 6. DROP
    if anomaly_status == "DROP":
        return "Investigate demand"

    # 7 & 8. NON_MOVING / SLOW_MOVING
    if movement_status == "NON_MOVING":
        return "Investigate demand"

    if movement_status == "SLOW_MOVING":
        return "Investigate demand"

    # 9. MEDIUM
    if stockout_risk == "MEDIUM":
        return "Monitor stock closely"

    # 10. UNKNOWN
    if stockout_risk == "UNKNOWN":
        return "Review demand history"

    # 11. default / SAFE / NORMAL
    return "No action needed"
