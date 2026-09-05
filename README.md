TRACK_ID=PS03
# StockSense AI

**AI-powered copilot for smarter sales and inventory decisions.**

## Project Overview
StockSense AI is an intelligent retail sales and inventory copilot built for store managers. It combines deterministic Python analytics over SQLite with natural language understanding via Gemini to deliver accurate, evidence-backed retail insights, detect stock-outs, overstocking, and sales anomalies, and recommend actionable operational steps.

## Problem Statement
Retail store managers face constant challenges managing stock levels, predicting demand, avoiding costly stock-outs, and identifying slow-moving inventory. Traditional tools are complex or lack grounded explanations. StockSense AI provides clear, data-backed recommendations and natural language interaction while relying strictly on deterministic business logic for calculations.

## Sample Dataset
StockSense AI includes a locally generated synthetic retail dataset for demonstration and evaluation.

Dataset contains:
- 3 fictional retail stores (Central Store Chennai, City Store Coimbatore, Market Store Madurai)
- 30 products across multiple categories (Dairy, Bakery, Beverages, Grocery, Snacks, Personal Care, Household, Stationery)
- Current inventory snapshots across all 90 store-product pairs
- Approximately 60 days of historical sales records (~6,000 transactions) ending 2026-09-05
- Deliberately generated demand patterns for testing analytics (high stock-out risk for Milk 1L, overstock for Bread, sales drop for Shampoo, sales spike for Coffee, non-moving inventory for Notebook, zero-stock and zero-recent-sales edge cases)

The dataset is synthetic and generated locally for hackathon demonstration purposes.

## Current Features & Development Status

### Completed
- **SQLite Retail Database**: Normalized 4-table schema (`Products`, `Stores`, `Inventory`, `Sales`) with strict validation constraints.
- **Deterministic Synthetic Dataset Generator**: 60 days of historical sales data with engineered retail patterns.
- **Multi-Page Application Shell**: Permanent 5-section navigation (`Dashboard`, `Inventory Intelligence`, `Sales Analytics`, `AI Copilot`, `Product Details`).
- **Live Dashboard Metrics**: Real-time KPI cards for Today's Revenue (INR), Today's Units Sold, Stock-out Risk, Overstocked Products, Slow-moving Products, and Sales Anomalies for latest sales date (`2026-09-05`).
- **Today's Priority Alerts**: Evidence-backed prioritized dashboard alerts combining stock-out risk, overstock, non-moving inventory, and sales anomalies (`SPIKE` / `DROP`).
- **Deterministic Inventory Intelligence Engine (`backend/inventory_engine.py`)**:
  - Average Daily Sales calculation over rolling 7-day window (returns `None` when recent units = 0)
  - Days Remaining calculation (`current_stock / avg_daily_sales`; returns `0` for stock = 0)
  - Stock-out Risk Classification (`OUT_OF_STOCK`, `CRITICAL`, `HIGH`, `MEDIUM`, `SAFE`, `UNKNOWN`)
  - Overstock Detection (`OVERSTOCK_RISK` when days remaining > 30)
  - Slow-moving and Non-moving Detection (`NON_MOVING` for 14d zero sales, `SLOW_MOVING` for <30% prior week velocity)
- **Deterministic Sales Analytics Engine (`backend/sales_engine.py`)**:
  - Period-over-period revenue growth % (`(current - prev) / prev * 100`; returns `None` if prev revenue = 0)
  - Store sales comparison and top-two store sales gap calculation
  - 30-day daily revenue trend and category sales performance breakdown
- **Deterministic Sales Anomaly Detection Engine (`backend/anomaly_engine.py`)**:
  - 7-day recent vs 21-day non-overlapping baseline sales velocity comparison
  - Sales Spike detection (`>= +50%` velocity increase)
  - Sales Drop detection (`<= -40%` velocity decrease)
  - Zero baseline protection (`INSUFFICIENT_BASELINE`, `percent_change = None`)
- **Centralized Canonical Recommendation Engine (`backend/recommendation_engine.py`)**: Strict priority mapping for inventory risks and sales anomalies.
- **AI Copilot & Query Router (`backend/query_router.py` & `backend/gemini_service.py`)**:
  - Natural language intent extraction using `gemini-3.5-flash-lite`
  - Grounded manager-facing explanations strictly backed by Python deterministic evidence payloads
  - Defensive JSON parsing and Numeric Grounding Safety validation (zero ungrounded numbers guarantee)
  - Lazy client initialization & deterministic fallback when API key is unconfigured
- **Product Details Drill-down Page**: Comprehensive product performance overview, 10 key metric cards, 30-day sales history chart, store inventory position table, and deterministic recommendation banner.
- **Edge-Case Handling & Evidence Safety**:
  - Stock > 0 with zero recent sales handled cleanly (`avg_daily_sales: None`, `days_remaining: None`, `stockout_risk: UNKNOWN`, `"N/A"` UI formatting, canonical note `MSG_NO_RECENT_SALES`).
  - Zero stock classified as `OUT_OF_STOCK` (`days_remaining: 0`, recommendation `"Replenish immediately"`, canonical note `MSG_ZERO_INVENTORY`).
  - Unknown products fail closed to `status: "insufficient_data"` with `"No recommendation available"` and catalog error message.
  - Out-of-domain queries map to `status: "unsupported"` with `"No recommendation available"` and standard out-of-scope finding.
  - Missing schema attributes (e.g., supplier) map to `status: "unsupported"` with recognized product evidence (`"Milk 1L"`) and missing attribute details.
  - Gemini API failure safeguards prevent zero tracebacks and skip LLM generation on unsupported payloads to guarantee zero hallucinations.

## Edge-Case Handling & Evidence Grounding

StockSense AI implements deterministic safeguards and defensive evidence handling for all edge cases across retail analytics and natural language AI Copilot interactions:

1. **Zero Recent Sales (`stock > 0`, `recent_7_units == 0`)**:
   - `calculate_avg_daily_sales()` returns `None`.
   - `calculate_days_remaining()` returns `None` (rendered as `"N/A"` in UI tables with zero-division protection).
   - `classify_stockout_risk()` evaluates to `UNKNOWN`.
   - Copilot payload includes canonical note: `"This product has recorded no recent sales, so a reliable stock-out estimate cannot be calculated."`

2. **Zero Inventory (`current_stock == 0`)**:
   - `calculate_days_remaining()` returns `0`.
   - `classify_stockout_risk()` evaluates to `OUT_OF_STOCK`.
   - `recommend_action()` returns `"Replenish immediately"`.
   - Copilot payload includes canonical note: `"Product is out of stock across all selected stores."`

3. **Unknown Product Fail-Closed (`"iPhone"`, `"Laptop"`)**:
   - 5-Stage Entity Resolver evaluates exact matches, normalized matches, substring matches, and high-confidence typo fuzzy matches (`difflib.get_close_matches` with `cutoff >= 0.80`).
   - Unrecognized items (such as `"iPhone"` or `"Laptop"`) fail closed to `status: "insufficient_data"`.
   - Finding returns: `"Product 'iPhone' was not found in the retail database catalog."`
   - Recommendation returns: `"No recommendation available"`.

4. **Out-of-Domain Query Safeguard (`"Who won the cricket match?"`)**:
   - Unrelated domain queries map to `status: "unsupported"`.
   - Finding returns: `"This question is outside the scope of retail sales and inventory management."`
   - Recommendation returns: `"No recommendation available"`.

5. **Missing Schema Attribute (`"Who supplies Milk?"`)**:
   - Schema attributes absent from the SQLite database (e.g. `supplier`) map to `status: "unsupported"`.
   - Entity resolver identifies the recognized product (`"Milk 1L"`).
   - Finding returns: `"Supplier information is not tracked in the current database schema."`
   - Evidence payload contains `{"recognized_product": "Milk 1L", "missing_attribute": "supplier"}`.
   - Recommendation returns: `"No recommendation available"`.

6. **Gemini API Failure & Fallback Safeguards**:
   - If `GEMINI_API_KEY` is unconfigured, invalid, or API calls fail, the Copilot automatically displays a fallback explanation banner without raising unhandled tracebacks.
   - For `unsupported` or `insufficient_data` queries, LLM synthesis is skipped entirely to prevent world-knowledge hallucinations.

## Technology Stack
- **Frontend / Dashboard**: Streamlit (Dark Theme)
- **Data Processing & Visualization**: Pandas, NumPy, Plotly
- **Database**: SQLite (Python `sqlite3`)
- **LLM Service**: Google Gemini API (`google-generativeai`)
- **Environment Management**: `python-dotenv`

## Project Structure
```text
StockSense-AI/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml
├── database/
│   └── retail.db
├── backend/
│   ├── __init__.py
│   ├── database.py
│   ├── inventory_engine.py
│   ├── sales_engine.py
│   ├── anomaly_engine.py
│   ├── recommendation_engine.py
│   ├── query_router.py
│   └── gemini_service.py
├── data/
│   ├── generate_dataset.py
│   ├── products.csv
│   ├── stores.csv
│   ├── inventory.csv
│   └── sales.csv
└── assets/
    └── logo.png
```

## Setup
1. Clone or navigate to the repository directory.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Generate the sample dataset:
   ```bash
   python data/generate_dataset.py
   ```

## Run Instructions
Start the application by executing:
```bash
python app.py
```
Then open your browser at:
[http://localhost:8000](http://localhost:8000)

## Environment Variables
Copy `.env.example` to `.env` and fill in the required keys:
```env
GEMINI_API_KEY=your_gemini_api_key_here
VALIDATION_KEY=your_validation_key_here
```

## Validation Key
The official hackathon validation key must be added to `.env` as `VALIDATION_KEY` before final submission. Do not invent or hardcode a validation key.
