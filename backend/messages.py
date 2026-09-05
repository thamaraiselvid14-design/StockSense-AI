"""Centralized User-Facing Backend Message Helpers for StockSense AI.

Defines exact canonical user-facing strings to avoid scattering wording logic across UI.
"""

MSG_NO_RECENT_SALES = (
    "This product has recorded no recent sales, so a reliable stock-out estimate cannot be calculated."
)

MSG_ZERO_INVENTORY = "Product is currently out of stock."

MSG_OUT_OF_DOMAIN = (
    "This question cannot be answered from the retail sales and inventory data available to StockSense AI."
)

MSG_MISSING_SUPPLIER_DATA = (
    "Supplier information is not available in the current dataset, so I cannot determine the cheapest supplier."
)

MSG_GEMINI_UNAVAILABLE = (
    "AI Copilot is temporarily unavailable — showing deterministic dashboard data instead"
)


def format_unknown_product_message(product_name: str) -> str:
    """Formats canonical unknown product finding message."""
    name_str = product_name if product_name else "specified name"
    return f"No product matching '{name_str}' exists in the current dataset."
