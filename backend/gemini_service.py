"""Gemini API Integration for StockSense AI.

Provides lazy Gemini client initialization, intent extraction, defensive JSON parsing,
grounded explanation generation, and numeric safety validation.
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv()

# Evaluator model setting with default gemini-3.5-flash-lite
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

ALLOWED_INTENTS = {
    "stockout_analysis",
    "overstock_analysis",
    "slow_moving_analysis",
    "sales_anomaly",
    "product_performance",
    "store_comparison",
    "general_today_summary",
    "unsupported",
    "insufficient_data",
}


def get_api_key():
    """Retrieves GEMINI_API_KEY from environment."""
    return os.getenv("GEMINI_API_KEY", "").strip()


def is_gemini_available():
    """Checks if GEMINI_API_KEY is configured and google.generativeai can be initialized safely."""
    key = get_api_key()
    if not key:
        return False
    try:
        import google.generativeai as genai

        genai.configure(api_key=key)
        return True
    except Exception:
        return False


def parse_json_safely(text: str) -> dict:
    """Defensively parses JSON from string, stripping markdown code blocks, backticks, and extra text."""
    if not text:
        return {"intent": "unsupported", "product": None, "store": None, "timeframe": None}

    cleaned = text.strip()

    # Strip code block fences if present
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned)
    cleaned = cleaned.strip()

    # Extract JSON object substring if surrounding text exists
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {"intent": "unsupported", "product": None, "store": None, "timeframe": None}


def _fallback_intent_extraction(user_question: str) -> dict:
    """Deterministic fallback intent classifier when Gemini API is unavailable or fails."""
    q = user_question.lower().strip()

    # Check for unsupported domains (suppliers, vendors, salaries, margins)
    if any(w in q for w in ["supplier", "supplies", "vendor", "manufacturer", "distributor", "wholesale", "cost price", "margin"]):
        return {
            "intent": "unsupported",
            "product": "Milk" if "milk" in q else None,
            "store": None,
            "timeframe": None,
        }

    # Default intent to unsupported if no retail keywords match
    intent = "unsupported"
    product = None
    store = None
    timeframe = None

    if any(w in q for w in ["stockout", "out of stock", "running out", "critical stock", "reorder"]):
        intent = "stockout_analysis"
    elif any(w in q for w in ["overstock", "excess", "too much stock", "surplus"]):
        intent = "overstock_analysis"
    elif any(w in q for w in ["slow moving", "non moving", "dead stock", "low sales", "not selling"]):
        intent = "slow_moving_analysis"
    elif any(w in q for w in ["anomaly", "anomalies", "spike", "drop", "unusual"]):
        intent = "sales_anomaly"
    elif any(w in q for w in ["compare", "store comparison", "best store", "which store", "sold the most"]):
        intent = "store_comparison"
    elif any(w in q for w in ["performance", "how did", "how is", "product sales", "revenue"]):
        intent = "product_performance"
    elif any(w in q for w in ["today", "overview", "dashboard", "summary", "attention"]):
        intent = "general_today_summary"

    # Known catalog products
    known_products = [
        "Milk 1L", "Bread", "Eggs 12pk", "Rice 5kg", "Sugar 1kg",
        "Coffee 200g", "Tea 250g", "Biscuits Pack", "Chips", "Soft Drink 750ml",
        "Juice 1L", "Shampoo 180ml", "Soap 100g", "Toothpaste 150g", "Detergent 1kg",
        "Dishwash Liquid 500ml", "Notebook", "Pen 5pk", "Butter 500g", "Paneer 200g",
        "Wheat Flour 5kg", "Cooking Oil 1L", "Turmeric Powder 200g", "Salt 1kg",
        "Instant Noodles", "Chocolate Bar", "Hand Wash 250ml", "Surface Cleaner 500ml",
        "Eraser Pack", "Marker Pen"
    ]

    # Search for known products (including short keywords like milk, coffee, shampoo, bread, etc.)
    short_keywords = {
        "milk": "Milk 1L", "bread": "Bread", "eggs": "Eggs 12pk", "rice": "Rice 5kg",
        "sugar": "Sugar 1kg", "coffee": "Coffee 200g", "tea": "Tea 250g", "shampoo": "Shampoo 180ml",
        "soap": "Soap 100g", "toothpaste": "Toothpaste 150g", "detergent": "Detergent 1kg",
        "butter": "Butter 500g", "paneer": "Paneer 200g", "salt": "Salt 1kg", "noodles": "Instant Noodles",
        "chocolate": "Chocolate Bar", "hand wash": "Hand Wash 250ml"
    }

    for kw, full_p in short_keywords.items():
        if kw in q:
            product = full_p
            break

    if not product:
        for kp in known_products:
            if kp.lower() in q:
                product = kp
                break

    # If no known product matched, extract target noun if user asked about a specific unknown product (e.g. iPhone)
    if not product and intent in ["product_performance", "store_comparison"]:
        m = re.search(r"(?:how is|how did|performance of|status of|about|sold the most)\s+([a-zA-Z0-9]+)", q)
        if m and m.group(1).lower() not in ["the", "a", "this", "product"]:
            product = m.group(1)

    # Extract store
    known_stores = ["downtown", "suburbs", "uptown", "s001", "s002", "s003"]
    for ks in known_stores:
        if ks in q:
            store = ks.title()
            break

    return {
        "intent": intent,
        "product": product,
        "store": store,
        "timeframe": timeframe,
    }


def extract_intent(user_question: str) -> dict:
    """Extracts intent and parameters from user question using Gemini API with defensive parsing."""
    if not user_question or not user_question.strip():
        return {"intent": "unsupported", "product": None, "store": None, "timeframe": None}

    if not is_gemini_available():
        return _fallback_intent_extraction(user_question)

    try:
        import google.generativeai as genai

        key = get_api_key()
        genai.configure(api_key=key)

        model_name = DEFAULT_MODEL
        model = genai.GenerativeModel(model_name)

        system_instruction = """You are an intent parser for StockSense AI.
Your only job is to classify a retail manager's question.
Return ONLY one valid JSON object.

Allowed intents:
- stockout_analysis
- overstock_analysis
- slow_moving_analysis
- sales_anomaly
- product_performance
- store_comparison
- general_today_summary
- unsupported
- insufficient_data

Extract product/store/timeframe only when explicitly present or clearly implied.

Expected JSON format:
{
  "intent": "<allowed_intent>",
  "product": "<product name or product_id or null>",
  "store": "<store name or store_id or 'all' or null>",
  "timeframe": "<current | this_month | last_30_days | null>"
}

Do not answer the user's question.
Do not calculate anything.
Do not explain your reasoning.
Do not output markdown.
Do not output code fences.
Do not invent product or store names."""

        prompt = f"{system_instruction}\n\nUser Question: {user_question}"
        response = model.generate_content(prompt)
        text = response.text if response and hasattr(response, "text") else ""

        parsed = parse_json_safely(text)

        # Validate intent field
        intent_val = parsed.get("intent")
        if intent_val not in ALLOWED_INTENTS:
            parsed["intent"] = "unsupported"

        return parsed

    except Exception as e:
        # Fallback to local rule-based parsing if API call fails
        fallback = _fallback_intent_extraction(user_question)
        fallback["api_error"] = str(e)
        return fallback


def generate_grounded_explanation(user_question: str, intent_data: dict, payload: dict) -> str:
    """Generates a natural manager-facing response strictly grounded in verified payload facts."""
    if not payload:
        return "No evidence data available to answer this query."

    # For unsupported or insufficient data queries, skip LLM generation to prevent world-knowledge hallucination
    p_status = payload.get("status") or payload.get("intent")
    if p_status in ["unsupported", "insufficient_data"]:
        return _generate_fallback_explanation(user_question, payload)

    if not is_gemini_available():
        return _generate_fallback_explanation(user_question, payload)

    try:
        import google.generativeai as genai

        key = get_api_key()
        genai.configure(api_key=key)

        model_name = DEFAULT_MODEL
        model = genai.GenerativeModel(model_name)

        payload_json = json.dumps(payload, indent=2)

        prompt = f"""You are an AI Retail Copilot for StockSense AI answering a manager's question.

CRITICAL CONSTRAINTS:
1. You MUST use ONLY the facts, numbers, metrics, and recommendations provided in the VERIFIED EVIDENCE PAYLOAD below.
2. Do NOT calculate any numbers (revenue, stock, percentages, days remaining).
3. Do NOT invent or extrapolate facts not directly present in the payload.
4. Always state the canonical recommendation provided in the payload.
5. Structure your response clearly using markdown sections:
   - **Finding**: Concise summary of what was identified.
   - **Recommended Action**: Canonical recommendation from payload.
   - **Assumptions**: State the assumptions field from payload.
   - **Evidence**: List key verified metrics and facts from payload.

User Question: {user_question}

VERIFIED EVIDENCE PAYLOAD:
{payload_json}

Provide a clear, manager-facing response grounded strictly in the payload above:"""

        response = model.generate_content(prompt)
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()
        else:
            return _generate_fallback_explanation(user_question, payload)

    except Exception:
        return _generate_fallback_explanation(user_question, payload)


def _generate_fallback_explanation(user_question: str, payload: dict) -> str:
    """Generates a structured deterministic response when Gemini is unavailable."""
    finding = payload.get("finding") or payload.get("summary") or "Analysis completed."
    rec = payload.get("recommendation") or payload.get("recommended_action") or "No action needed"
    assumption = payload.get("assumption") or payload.get("assumptions") or "Standard deterministic calculations applied."

    evidence = payload.get("evidence", {})
    details = payload.get("details", [])
    if isinstance(evidence, dict) and "details" in evidence and evidence["details"]:
        details = evidence["details"]

    detail_lines = []

    if isinstance(details, list) and details:
        for d in details[:5]:
            if isinstance(d, dict):
                p_name = d.get("product") or d.get("product_name") or d.get("product_id") or "Product"
                st_name = d.get("store") or d.get("store_name") or "Store"
                stock = d.get("current_stock")
                days_rem = d.get("days_remaining")
                days_str = f"{days_rem:.1f} days" if isinstance(days_rem, (int, float)) else "N/A"
                if stock is not None:
                    detail_lines.append(f"- **{p_name}** ({st_name}): Current stock: {stock} units | Days remaining: {days_str}")
                else:
                    rev = d.get("revenue") or d.get("total_revenue") or d.get("30d_revenue")
                    units = d.get("units_sold") or d.get("30d_units_sold")
                    if rev is not None and units is not None:
                        detail_lines.append(f"- **{p_name}** ({st_name}): Units sold: {units} | Revenue ₹{rev:,.2f}")
                    elif rev is not None:
                        detail_lines.append(f"- **{p_name}**: Revenue ₹{rev:,.2f}")
                    elif units is not None:
                        detail_lines.append(f"- **{p_name}** ({st_name}): Units sold: {units}")
                    else:
                        detail_lines.append(f"- **{p_name}** ({st_name})")

    details_str = "\n".join(detail_lines) if detail_lines else "No specific item details."

    return f"""**Finding:** {finding}

**Recommended Action:** `{rec}`

**Assumptions:** {assumption}

**Verified Evidence Metrics:**
{details_str}
"""


def _extract_numbers_from_payload(obj) -> set:
    """Recursively extracts all numeric values (as formatted strings and floats) from payload dictionary."""
    valid_numbers = set()

    def _walk(item):
        if isinstance(item, (int, float)):
            valid_numbers.add(str(item))
            valid_numbers.add(f"{item:.1f}")
            valid_numbers.add(f"{item:.2f}")
            valid_numbers.add(f"{int(item)}")
        elif isinstance(item, str):
            # Extract digits/numbers embedded in string fields
            nums = re.findall(r"\b\d+(?:\.\d+)?\b", item)
            for n in nums:
                valid_numbers.add(n)
                try:
                    f = float(n)
                    valid_numbers.add(f"{f:.1f}")
                    valid_numbers.add(f"{f:.2f}")
                    valid_numbers.add(f"{int(f)}")
                except ValueError:
                    pass
        elif isinstance(item, dict):
            for v in item.values():
                _walk(v)
        elif isinstance(item, list):
            for v in item:
                _walk(v)

    _walk(obj)

    # Allow common business constants (windows, day counts, top N)
    common_constants = {"1", "2", "3", "5", "7", "10", "14", "21", "30", "60", "90", "0"}
    valid_numbers.update(common_constants)
    return valid_numbers


def validate_numeric_safety(explanation_text: str, payload: dict) -> dict:
    """Validates that numbers mentioned in explanation_text originate from payload facts."""
    if not explanation_text or not payload:
        return {"is_safe": True, "ungrounded_numbers": [], "explanation": explanation_text}

    payload_numbers = _extract_numbers_from_payload(payload)

    # Strip commas from numbers like 44,220.00 -> 44220.00
    cleaned_text = re.sub(r"(\d+),(\d+)", r"\1\2", explanation_text)

    # Find all numeric instances in cleaned explanation text
    found_nums = re.findall(r"\b\d+(?:\.\d+)?\b", cleaned_text)

    ungrounded = []
    for num_str in found_nums:
        if num_str in payload_numbers:
            continue
        try:
            val = float(num_str)
            val_1f = f"{val:.1f}"
            val_2f = f"{val:.2f}"
            val_int = f"{int(val)}"
            if (
                val_1f in payload_numbers
                or val_2f in payload_numbers
                or val_int in payload_numbers
            ):
                continue
        except ValueError:
            pass

        ungrounded.append(num_str)

    # Remove duplicates preserving order
    unique_ungrounded = list(dict.fromkeys(ungrounded))

    return {
        "is_safe": len(unique_ungrounded) == 0,
        "ungrounded_numbers": unique_ungrounded,
        "explanation": explanation_text,
    }
