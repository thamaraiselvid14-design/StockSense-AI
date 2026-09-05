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
- **Live Dashboard Metrics**: Real-time KPI cards for Today's Revenue (INR), Today's Units Sold, and Stock-out Risk count for the latest sales date (`2026-09-05`).
- **30-Day Revenue Visualization**: Responsive Plotly line chart rendering daily revenue trend from SQLite.
- **Top Product Visualization**: Plotly horizontal bar chart highlighting top 10 products by revenue.
- **Inventory Intelligence Page**: Complete inventory table with store, category, and product search filters, 7-day average daily sales, and days remaining calculations.
- **Strict UI Architecture**: Zero raw SQL queries inside UI code; all database interactions routed through semantic `backend/database.py` functions.

### Upcoming
- Advanced stock-out risk classification (days-remaining algorithms)
- Overstock detection engine
- Slow-moving and non-moving inventory detection engine
- Sales anomaly detection engine (spikes and drops)
- Evidence-based recommendation engine
- Gemini AI Copilot natural language query router and grounded explanations

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
│   ├── sales_engine.py
│   ├── inventory_engine.py
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
