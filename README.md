TRACK_ID=PS03
# StockSense AI

**AI-powered copilot for smarter sales and inventory decisions.**

## Project Overview
StockSense AI is an intelligent retail sales and inventory copilot built for store managers. It combines deterministic Python analytics over SQLite with natural language understanding via Gemini to deliver accurate, evidence-backed retail insights, detect stock-outs, overstocking, and sales anomalies, and recommend actionable operational steps.

## Problem Statement
Retail store managers face constant challenges managing stock levels, predicting demand, avoiding costly stock-outs, and identifying slow-moving inventory. Traditional tools are complex or lack grounded explanations. StockSense AI provides clear, data-backed recommendations and natural language interaction while relying strictly on deterministic business logic for calculations.

## Planned Features
- **Deterministic Analytics Engine**: Exact calculations for sales performance, stock levels, stock-out risk, overstocking, and slow-moving items.
- **Anomaly Detection Engine**: Automatic identification of unusual sales spikes and drops.
- **Evidence-Based Recommendation Engine**: Actionable operational suggestions grounded strictly in empirical data.
- **AI Copilot**: Natural language query router and grounded explanation powered by Gemini.
- **Interactive Dark Dashboard**: Real-time KPI summary, priorities, trends, and inventory health visuals.

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

## Current Development Status
- **Phase 0 (Completed)**: Project skeleton, directory structure, placeholder backend modules, empty database and data files, dark Streamlit starter theme, and entry point.
- **Phase 1 (Upcoming)**: Database schema creation and sample dataset generation.

## Validation Key
The official hackathon validation key must be added to `.env` as `VALIDATION_KEY` before final submission. Do not invent or hardcode a validation key.
