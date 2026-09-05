"""SQLite database connection, initialization, and query utilities for StockSense AI."""

from datetime import datetime, timedelta
import os
import sqlite3

# Define relative path to retail.db from backend package location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "retail.db")


def get_connection():
    """Locates retail.db using a project-relative path, opens connection,

    enables foreign keys, and sets Row row_factory.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creates the four business tables if they do not exist."""
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS Products (
                product_id TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0)
            )
            """
            )

            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS Stores (
                store_id TEXT PRIMARY KEY,
                store_name TEXT NOT NULL,
                location TEXT NOT NULL
            )
            """
            )

            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS Inventory (
                inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                current_stock INTEGER NOT NULL CHECK (current_stock >= 0),
                last_updated TEXT NOT NULL,
                FOREIGN KEY (store_id) REFERENCES Stores(store_id),
                FOREIGN KEY (product_id) REFERENCES Products(product_id),
                UNIQUE(store_id, product_id)
            )
            """
            )

            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS Sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                store_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                revenue REAL NOT NULL CHECK (revenue >= 0),
                FOREIGN KEY (store_id) REFERENCES Stores(store_id),
                FOREIGN KEY (product_id) REFERENCES Products(product_id)
            )
            """
            )
    finally:
        conn.close()


def fetch_all(query, params=()):
    """Executes parameterized query and returns all matching rows."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()


def fetch_one(query, params=()):
    """Executes parameterized query and returns a single matching row or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row
    finally:
        conn.close()


def execute_query(query, params=()):
    """Executes parameterized DML query (INSERT, UPDATE, DELETE) and commits."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
    finally:
        conn.close()


def execute_many(query, seq_of_params=()):
    """Executes parameterized query against a sequence of parameter tuples and commits."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.executemany(query, seq_of_params)
            return cursor.rowcount
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# SEMANTIC DATABASE QUERY FUNCTIONS FOR PHASE 2 (NO RAW SQL IN UI)
# -----------------------------------------------------------------------------


def get_database_counts():
    """Returns dictionary with table row counts and connection status for retail.db."""
    try:
        prod_row = fetch_one("SELECT COUNT(*) FROM Products")
        store_row = fetch_one("SELECT COUNT(*) FROM Stores")
        inv_row = fetch_one("SELECT COUNT(*) FROM Inventory")
        sales_row = fetch_one("SELECT COUNT(*) FROM Sales")

        if (
            prod_row is not None
            and store_row is not None
            and inv_row is not None
            and sales_row is not None
        ):
            return {
                "connected": True,
                "products": prod_row[0],
                "stores": store_row[0],
                "inventory": inv_row[0],
                "sales": sales_row[0],
            }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "products": 0,
            "stores": 0,
            "inventory": 0,
            "sales": 0,
        }

    return {
        "connected": False,
        "error": "Database not initialized",
        "products": 0,
        "stores": 0,
        "inventory": 0,
        "sales": 0,
    }


def get_latest_sales_date():
    """Returns the latest available sales date string (YYYY-MM-DD) from SQLite, or None."""
    row = fetch_one("SELECT MAX(date) FROM Sales")
    return row[0] if row and row[0] else None


def get_dashboard_kpis():
    """Returns today's revenue, today's units sold, stock-out risk count, and latest sales date."""
    latest_date = get_latest_sales_date()
    if not latest_date:
        return {
            "latest_date": None,
            "todays_revenue": 0.0,
            "todays_units": 0,
            "low_stock_count": 0,
        }

    rev_row = fetch_one(
        "SELECT COALESCE(SUM(revenue), 0) FROM Sales WHERE date = ?",
        (latest_date,),
    )
    units_row = fetch_one(
        "SELECT COALESCE(SUM(quantity), 0) FROM Sales WHERE date = ?",
        (latest_date,),
    )

    # Temporary Phase 2 stock-out risk: count of inventory positions where current_stock < reorder_level
    risk_row = fetch_one(
        """
        SELECT COUNT(*)
        FROM Inventory i
        JOIN Products p ON i.product_id = p.product_id
        WHERE i.current_stock < p.reorder_level
        """
    )

    return {
        "latest_date": latest_date,
        "todays_revenue": float(rev_row[0]) if rev_row else 0.0,
        "todays_units": int(units_row[0]) if units_row else 0,
        "low_stock_count": int(risk_row[0]) if risk_row else 0,
    }


def get_revenue_trend(days=30):
    """Returns daily revenue for the latest 'days' sales dates ending on latest_sales_date."""
    latest_date = get_latest_sales_date()
    if not latest_date:
        return []

    rows = fetch_all(
        """
        SELECT date, SUM(revenue) as revenue
        FROM Sales
        WHERE date IN (
            SELECT DISTINCT date FROM Sales WHERE date <= ? ORDER BY date DESC LIMIT ?
        )
        GROUP BY date
        ORDER BY date ASC
        """,
        (latest_date, days),
    )

    return [{"date": row["date"], "revenue": float(row["revenue"])} for row in rows]


def get_top_products_by_revenue(days=30, limit=10):
    """Returns top N products aggregated by revenue over the latest 'days' sales dates."""
    latest_date = get_latest_sales_date()
    if not latest_date:
        return []

    rows = fetch_all(
        """
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
        ORDER BY total_revenue DESC
        LIMIT ?
        """,
        (latest_date, days, limit),
    )

    return [
        {
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "category": row["category"],
            "total_revenue": float(row["total_revenue"]),
            "total_units": int(row["total_units"]),
        }
        for row in rows
    ]


def get_inventory_intelligence(days=7):
    """Returns all store/product inventory positions with 7-day sales totals and stock info."""
    latest_date = get_latest_sales_date()
    if not latest_date:
        return []

    ref_date = datetime.strptime(latest_date, "%Y-%m-%d")
    start_date_str = (ref_date - timedelta(days=days - 1)).strftime("%Y-%m-%d")

    rows = fetch_all(
        """
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            p.price,
            p.reorder_level,
            s.store_id,
            s.store_name,
            s.location,
            i.current_stock,
            i.last_updated,
            COALESCE(sales_7d.recent_units_sold, 0) as recent_7d_units
        FROM Inventory i
        JOIN Products p ON i.product_id = p.product_id
        JOIN Stores s ON i.store_id = s.store_id
        LEFT JOIN (
            SELECT store_id, product_id, SUM(quantity) as recent_units_sold
            FROM Sales
            WHERE date >= ? AND date <= ?
            GROUP BY store_id, product_id
        ) sales_7d ON i.store_id = sales_7d.store_id AND i.product_id = sales_7d.product_id
        ORDER BY s.store_id ASC, p.product_id ASC
        """,
        (start_date_str, latest_date),
    )

    result = []
    for row in rows:
        recent_units = int(row["recent_7d_units"])
        avg_daily_sales = recent_units / float(days)

        result.append(
            {
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "price": float(row["price"]),
                "reorder_level": int(row["reorder_level"]),
                "store_id": row["store_id"],
                "store_name": row["store_name"],
                "location": row["location"],
                "current_stock": int(row["current_stock"]),
                "last_updated": row["last_updated"],
                "recent_7d_units": recent_units,
                "avg_daily_sales": avg_daily_sales,
            }
        )

    return result


def get_categories():
    """Returns list of distinct product categories sorted alphabetically."""
    rows = fetch_all("SELECT DISTINCT category FROM Products ORDER BY category ASC")
    return [row["category"] for row in rows]


def get_stores_list():
    """Returns list of all stores sorted by store_id."""
    rows = fetch_all("SELECT store_id, store_name, location FROM Stores ORDER BY store_id ASC")
    return [dict(row) for row in rows]
