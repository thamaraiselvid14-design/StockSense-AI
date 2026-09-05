"""Synthetic dataset generator for StockSense AI.

Generates 3 stores, 30 products, 90 inventory snapshots, and ~60 days of historical sales data
with deliberate engineered demand patterns for analytics testing.
Exports data to both SQLite (database/retail.db) and CSV files (data/*.csv).
"""

import csv
from datetime import datetime, timedelta
import os
import random
import sys
import numpy as np

# Ensure backend package can be imported when running script directly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import get_connection, init_db

# Reference date for hackathon timeline
REFERENCE_DATE_STR = "2026-09-05"
REFERENCE_DATE = datetime.strptime(REFERENCE_DATE_STR, "%Y-%m-%d")
NUM_DAYS = 60
START_DATE = REFERENCE_DATE - timedelta(days=NUM_DAYS - 1)

DATA_DIR = os.path.join(BASE_DIR, "data")


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)


def get_stores():
    return [
        {
            "store_id": "S001",
            "store_name": "Central Store",
            "location": "Chennai",
        },
        {"store_id": "S002", "store_name": "City Store", "location": "Coimbatore"},
        {
            "store_id": "S003",
            "store_name": "Market Store",
            "location": "Madurai",
        },
    ]


def get_products():
    return [
        {
            "product_id": "P001",
            "product_name": "Milk 1L",
            "category": "Dairy",
            "price": 60.0,
            "reorder_level": 50,
        },
        {
            "product_id": "P002",
            "product_name": "Bread",
            "category": "Bakery",
            "price": 40.0,
            "reorder_level": 20,
        },
        {
            "product_id": "P003",
            "product_name": "Eggs 12pk",
            "category": "Dairy",
            "price": 90.0,
            "reorder_level": 30,
        },
        {
            "product_id": "P004",
            "product_name": "Rice 5kg",
            "category": "Grocery",
            "price": 350.0,
            "reorder_level": 15,
        },
        {
            "product_id": "P005",
            "product_name": "Sugar 1kg",
            "category": "Grocery",
            "price": 45.0,
            "reorder_level": 25,
        },
        {
            "product_id": "P006",
            "product_name": "Coffee 200g",
            "category": "Beverages",
            "price": 180.0,
            "reorder_level": 20,
        },
        {
            "product_id": "P007",
            "product_name": "Tea 250g",
            "category": "Beverages",
            "price": 120.0,
            "reorder_level": 25,
        },
        {
            "product_id": "P008",
            "product_name": "Biscuits Pack",
            "category": "Snacks",
            "price": 30.0,
            "reorder_level": 40,
        },
        {
            "product_id": "P009",
            "product_name": "Chips",
            "category": "Snacks",
            "price": 20.0,
            "reorder_level": 50,
        },
        {
            "product_id": "P010",
            "product_name": "Soft Drink 750ml",
            "category": "Beverages",
            "price": 40.0,
            "reorder_level": 30,
        },
        {
            "product_id": "P011",
            "product_name": "Juice 1L",
            "category": "Beverages",
            "price": 85.0,
            "reorder_level": 20,
        },
        {
            "product_id": "P012",
            "product_name": "Shampoo 180ml",
            "category": "Personal Care",
            "price": 220.0,
            "reorder_level": 15,
        },
        {
            "product_id": "P013",
            "product_name": "Soap 100g",
            "category": "Personal Care",
            "price": 35.0,
            "reorder_level": 40,
        },
        {
            "product_id": "P014",
            "product_name": "Toothpaste 150g",
            "category": "Personal Care",
            "price": 85.0,
            "reorder_level": 25,
        },
        {
            "product_id": "P015",
            "product_name": "Detergent 1kg",
            "category": "Household",
            "price": 150.0,
            "reorder_level": 20,
        },
        {
            "product_id": "P016",
            "product_name": "Dishwash Liquid 500ml",
            "category": "Household",
            "price": 110.0,
            "reorder_level": 15,
        },
        {
            "product_id": "P017",
            "product_name": "Notebook",
            "category": "Stationery",
            "price": 65.0,
            "reorder_level": 30,
        },
        {
            "product_id": "P018",
            "product_name": "Pen 5pk",
            "category": "Stationery",
            "price": 15.0,
            "reorder_level": 50,
        },
        {
            "product_id": "P019",
            "product_name": "Butter 500g",
            "category": "Dairy",
            "price": 275.0,
            "reorder_level": 20,
        },
        {
            "product_id": "P020",
            "product_name": "Paneer 200g",
            "category": "Dairy",
            "price": 120.0,
            "reorder_level": 15,
        },
        {
            "product_id": "P021",
            "product_name": "Wheat Flour 5kg",
            "category": "Grocery",
            "price": 260.0,
            "reorder_level": 20,
        },
        {
            "product_id": "P022",
            "product_name": "Cooking Oil 1L",
            "category": "Grocery",
            "price": 175.0,
            "reorder_level": 25,
        },
        {
            "product_id": "P023",
            "product_name": "Turmeric Powder 200g",
            "category": "Grocery",
            "price": 60.0,
            "reorder_level": 15,
        },
        {
            "product_id": "P024",
            "product_name": "Salt 1kg",
            "category": "Grocery",
            "price": 25.0,
            "reorder_level": 30,
        },
        {
            "product_id": "P025",
            "product_name": "Instant Noodles",
            "category": "Snacks",
            "price": 28.0,
            "reorder_level": 40,
        },
        {
            "product_id": "P026",
            "product_name": "Chocolate Bar",
            "category": "Snacks",
            "price": 50.0,
            "reorder_level": 30,
        },
        {
            "product_id": "P027",
            "product_name": "Hand Wash 250ml",
            "category": "Personal Care",
            "price": 95.0,
            "reorder_level": 20,
        },
        {
            "product_id": "P028",
            "product_name": "Surface Cleaner 500ml",
            "category": "Household",
            "price": 130.0,
            "reorder_level": 15,
        },
        {
            "product_id": "P029",
            "product_name": "Eraser Pack",
            "category": "Stationery",
            "price": 20.0,
            "reorder_level": 30,
        },
        {
            "product_id": "P030",
            "product_name": "Marker Pen",
            "category": "Stationery",
            "price": 40.0,
            "reorder_level": 25,
        },
    ]


def generate_inventory(stores, products):
    """Generates 90 inventory records with engineered patterns."""
    inventory = []
    inventory_id = 1

    for store in stores:
        s_id = store["store_id"]

        for prod in products:
            p_id = prod["product_id"]

            # Pattern A: Milk 1L (P001) - Stock-out risk (low current stock)
            if p_id == "P001":
                if s_id == "S001":
                    stock = 18
                elif s_id == "S002":
                    stock = 15
                else:
                    stock = 20

            # Pattern B: Bread (P002) - Overstock (low demand, high current stock)
            elif p_id == "P002":
                if s_id == "S001":
                    stock = 180
                elif s_id == "S002":
                    stock = 200
                else:
                    stock = 160

            # Pattern F: Out-of-stock edge case (current_stock = 0 for P015 in S002)
            elif p_id == "P015" and s_id == "S002":
                stock = 0

            # Pattern E: Notebook (P017) - Non-moving inventory (stock > 0, 0 sales in 14 days)
            elif p_id == "P017":
                stock = 45

            # Pattern G: Marker Pen (P030) - Zero recent 7-day sales (stock > 0)
            elif p_id == "P030":
                stock = 30

            # Shampoo (P012) & Coffee (P006) - Normal inventory
            elif p_id == "P012":
                stock = 50
            elif p_id == "P006":
                stock = 60

            # Normal products: varied stock between 35 and 90
            else:
                stock = random.randint(35, 90)

            inventory.append(
                {
                    "inventory_id": inventory_id,
                    "store_id": s_id,
                    "product_id": p_id,
                    "current_stock": stock,
                    "last_updated": REFERENCE_DATE_STR,
                }
            )
            inventory_id += 1

    return inventory


def generate_sales(stores, products):
    """Generates ~60 days of sales history with engineered patterns."""
    sales = []
    sale_id = 1

    price_map = {p["product_id"]: p["price"] for p in products}

    date_list = [START_DATE + timedelta(days=i) for i in range(NUM_DAYS)]

    for current_date in date_list:
        date_str = current_date.strftime("%Y-%m-%d")
        days_from_start = (current_date - START_DATE).days  # 0 to 59
        days_to_ref = (REFERENCE_DATE - current_date).days  # 59 down to 0

        is_weekend = current_date.weekday() >= 5  # Sat (5), Sun (6)

        for store in stores:
            s_id = store["store_id"]

            for prod in products:
                p_id = prod["product_id"]
                unit_price = price_map[p_id]

                # Pattern A: Milk 1L (P001) - Consistently strong sales, especially recent 7 days
                if p_id == "P001":
                    if days_to_ref < 7:  # Recent 7 days (Aug 30 - Sep 5)
                        # 2 sale records per store per day with high quantity
                        qty1 = random.randint(5, 8)
                        qty2 = random.randint(4, 7)
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty1,
                                "unit_price": unit_price,
                                "revenue": round(qty1 * unit_price, 2),
                            }
                        )
                        sale_id += 1
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty2,
                                "unit_price": unit_price,
                                "revenue": round(qty2 * unit_price, 2),
                            }
                        )
                        sale_id += 1
                    else:
                        # Baseline days (days 0 to 52)
                        qty = random.randint(7, 11)
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty,
                                "unit_price": unit_price,
                                "revenue": round(qty * unit_price, 2),
                            }
                        )
                        sale_id += 1

                # Pattern B: Bread (P002) - Low sales velocity (~1-3 units/day)
                elif p_id == "P002":
                    if random.random() < 0.7:  # 70% chance of a sale
                        qty = random.randint(1, 3)
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty,
                                "unit_price": unit_price,
                                "revenue": round(qty * unit_price, 2),
                            }
                        )
                        sale_id += 1

                # Pattern C: Shampoo (P012) - Sales Drop (steady 7 weeks, 50-70% drop final 10 days)
                elif p_id == "P012":
                    if days_to_ref < 10:  # Final 10 days (Aug 27 - Sep 5)
                        if (
                            random.random() < 0.6
                        ):  # Lower frequency & lower qty
                            qty = random.randint(1, 3)  # ~2-3 units/day average
                            sales.append(
                                {
                                    "sale_id": sale_id,
                                    "date": date_str,
                                    "store_id": s_id,
                                    "product_id": p_id,
                                    "quantity": qty,
                                    "unit_price": unit_price,
                                    "revenue": round(qty * unit_price, 2),
                                }
                            )
                            sale_id += 1
                    else:
                        # Baseline first 50 days: steady moderate sales (~8-10 units/day)
                        qty1 = random.randint(4, 6)
                        qty2 = random.randint(4, 5)
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty1,
                                "unit_price": unit_price,
                                "revenue": round(qty1 * unit_price, 2),
                            }
                        )
                        sale_id += 1
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty2,
                                "unit_price": unit_price,
                                "revenue": round(qty2 * unit_price, 2),
                            }
                        )
                        sale_id += 1

                # Pattern D: Coffee (P006) - Sales Spike (stable baseline, 2-3x spike final 5 days)
                elif p_id == "P006":
                    if days_to_ref < 5:  # Final 5 days (Sep 1 - Sep 5)
                        qty1 = random.randint(6, 8)
                        qty2 = random.randint(6, 7)  # ~12-15 units/day
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty1,
                                "unit_price": unit_price,
                                "revenue": round(qty1 * unit_price, 2),
                            }
                        )
                        sale_id += 1
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty2,
                                "unit_price": unit_price,
                                "revenue": round(qty2 * unit_price, 2),
                            }
                        )
                        sale_id += 1
                    else:
                        # Baseline first 55 days (~5 units/day)
                        qty = random.randint(4, 6)
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty,
                                "unit_price": unit_price,
                                "revenue": round(qty * unit_price, 2),
                            }
                        )
                        sale_id += 1

                # Pattern E: Notebook (P017) - Non-moving inventory (ZERO sales final 14 days)
                elif p_id == "P017":
                    if days_to_ref >= 14:  # Only generate sales BEFORE final 14 days
                        if random.random() < 0.7:
                            qty = random.randint(2, 4)
                            sales.append(
                                {
                                    "sale_id": sale_id,
                                    "date": date_str,
                                    "store_id": s_id,
                                    "product_id": p_id,
                                    "quantity": qty,
                                    "unit_price": unit_price,
                                    "revenue": round(qty * unit_price, 2),
                                }
                            )
                            sale_id += 1

                # Pattern G: Marker Pen (P030) - Zero sales final 7 days
                elif p_id == "P030":
                    if days_to_ref >= 7:  # Only generate sales BEFORE final 7 days
                        if random.random() < 0.7:
                            qty = random.randint(1, 3)
                            sales.append(
                                {
                                    "sale_id": sale_id,
                                    "date": date_str,
                                    "store_id": s_id,
                                    "product_id": p_id,
                                    "quantity": qty,
                                    "unit_price": unit_price,
                                    "revenue": round(qty * unit_price, 2),
                                }
                            )
                            sale_id += 1

                # Normal products: realistic variation
                else:
                    prob = 0.95 if is_weekend else 0.88
                    if random.random() < prob:
                        qty = random.randint(1, 4)
                        sales.append(
                            {
                                "sale_id": sale_id,
                                "date": date_str,
                                "store_id": s_id,
                                "product_id": p_id,
                                "quantity": qty,
                                "unit_price": unit_price,
                                "revenue": round(qty * unit_price, 2),
                            }
                        )
                        sale_id += 1

                        # Second sale transaction for fast-moving items or weekend traffic
                        if (is_weekend and random.random() < 0.45) or (not is_weekend and random.random() < 0.25):
                            qty2 = random.randint(1, 3)
                            sales.append(
                                {
                                    "sale_id": sale_id,
                                    "date": date_str,
                                    "store_id": s_id,
                                    "product_id": p_id,
                                    "quantity": qty2,
                                    "unit_price": unit_price,
                                    "revenue": round(qty2 * unit_price, 2),
                                }
                            )
                            sale_id += 1

    return sales


def save_to_database(stores, products, inventory, sales):
    """Safely populates SQLite database inside a transaction (clearing existing synthetic records)."""
    conn = get_connection()
    try:
        with conn:
            cursor = conn.cursor()

            # Delete existing records in foreign key order
            cursor.execute("DELETE FROM Sales")
            cursor.execute("DELETE FROM Inventory")
            cursor.execute("DELETE FROM Products")
            cursor.execute("DELETE FROM Stores")

            # Insert Stores
            cursor.executemany(
                "INSERT INTO Stores (store_id, store_name, location) VALUES (?, ?, ?)",
                [(s["store_id"], s["store_name"], s["location"]) for s in stores],
            )

            # Insert Products
            cursor.executemany(
                "INSERT INTO Products (product_id, product_name, category, price, reorder_level) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        p["product_id"],
                        p["product_name"],
                        p["category"],
                        p["price"],
                        p["reorder_level"],
                    )
                    for p in products
                ],
            )

            # Insert Inventory
            cursor.executemany(
                "INSERT INTO Inventory (inventory_id, store_id, product_id, current_stock, last_updated) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        inv["inventory_id"],
                        inv["store_id"],
                        inv["product_id"],
                        inv["current_stock"],
                        inv["last_updated"],
                    )
                    for inv in inventory
                ],
            )

            # Insert Sales
            cursor.executemany(
                "INSERT INTO Sales (sale_id, date, store_id, product_id, quantity, unit_price, revenue) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        s["sale_id"],
                        s["date"],
                        s["store_id"],
                        s["product_id"],
                        s["quantity"],
                        s["unit_price"],
                        s["revenue"],
                    )
                    for s in sales
                ],
            )
    finally:
        conn.close()


def save_to_csv(stores, products, inventory, sales):
    """Exports dataset to CSV files."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # products.csv
    with open(
        os.path.join(DATA_DIR, "products.csv"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "product_id",
                "product_name",
                "category",
                "price",
                "reorder_level",
            ],
        )
        writer.writeheader()
        writer.writerows(products)

    # stores.csv
    with open(
        os.path.join(DATA_DIR, "stores.csv"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=["store_id", "store_name", "location"]
        )
        writer.writeheader()
        writer.writerows(stores)

    # inventory.csv
    with open(
        os.path.join(DATA_DIR, "inventory.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "inventory_id",
                "store_id",
                "product_id",
                "current_stock",
                "last_updated",
            ],
        )
        writer.writeheader()
        writer.writerows(inventory)

    # sales.csv
    with open(
        os.path.join(DATA_DIR, "sales.csv"), "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sale_id",
                "date",
                "store_id",
                "product_id",
                "quantity",
                "unit_price",
                "revenue",
            ],
        )
        writer.writeheader()
        writer.writerows(sales)


def validate_dataset():
    """Programmatically validates SQLite database constraints, counts, and dates."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Counts
        stores_cnt = cursor.execute("SELECT COUNT(*) FROM Stores").fetchone()[0]
        prod_cnt = cursor.execute("SELECT COUNT(*) FROM Products").fetchone()[0]
        inv_cnt = cursor.execute("SELECT COUNT(*) FROM Inventory").fetchone()[0]
        sales_cnt = cursor.execute("SELECT COUNT(*) FROM Sales").fetchone()[0]

        assert stores_cnt == 3, f"Expected 3 stores, got {stores_cnt}"
        assert prod_cnt == 30, f"Expected 30 products, got {prod_cnt}"
        assert inv_cnt == 90, f"Expected 90 inventory rows, got {inv_cnt}"
        assert (
            5000 <= sales_cnt <= 10000
        ), f"Expected 5,000–10,000 sales rows, got {sales_cnt}"

        # Constraint Checks
        neg_stock = cursor.execute(
            "SELECT COUNT(*) FROM Inventory WHERE current_stock < 0"
        ).fetchone()[0]
        assert neg_stock == 0, "Found negative stock values"

        neg_price = cursor.execute(
            "SELECT COUNT(*) FROM Products WHERE price < 0"
        ).fetchone()[0]
        assert neg_price == 0, "Found negative product prices"

        inv_qty = cursor.execute(
            "SELECT COUNT(*) FROM Sales WHERE quantity <= 0"
        ).fetchone()[0]
        assert inv_qty == 0, "Found non-positive sales quantities"

        neg_rev = cursor.execute(
            "SELECT COUNT(*) FROM Sales WHERE revenue < 0"
        ).fetchone()[0]
        assert neg_rev == 0, "Found negative revenue values"

        # Foreign Key / Orphan Checks
        orphan_store_inv = cursor.execute(
            "SELECT COUNT(*) FROM Inventory WHERE store_id NOT IN (SELECT store_id FROM Stores)"
        ).fetchone()[0]
        assert orphan_store_inv == 0, "Found orphan store_id in Inventory"

        orphan_prod_inv = cursor.execute(
            "SELECT COUNT(*) FROM Inventory WHERE product_id NOT IN (SELECT product_id FROM Products)"
        ).fetchone()[0]
        assert orphan_prod_inv == 0, "Found orphan product_id in Inventory"

        orphan_sales_store = cursor.execute(
            "SELECT COUNT(*) FROM Sales WHERE store_id NOT IN (SELECT store_id FROM Stores)"
        ).fetchone()[0]
        assert orphan_sales_store == 0, "Found orphan store_id in Sales"

        orphan_sales_prod = cursor.execute(
            "SELECT COUNT(*) FROM Sales WHERE product_id NOT IN (SELECT product_id FROM Products)"
        ).fetchone()[0]
        assert orphan_sales_prod == 0, "Found orphan product_id in Sales"

        # Duplicate check
        dup_inv = cursor.execute(
            "SELECT store_id, product_id, COUNT(*) FROM Inventory GROUP BY store_id, product_id HAVING COUNT(*) > 1"
        ).fetchall()
        assert len(dup_inv) == 0, "Found duplicate store/product inventory pairs"

        # Revenue match check (revenue == round(quantity * unit_price, 2))
        mismatch_rev = cursor.execute(
            "SELECT COUNT(*) FROM Sales WHERE ABS(revenue - (quantity * unit_price)) > 0.01"
        ).fetchone()[0]
        assert mismatch_rev == 0, "Found revenue calculation mismatches"

        # Date range check
        min_date, max_date = cursor.execute(
            "SELECT MIN(date), MAX(date) FROM Sales"
        ).fetchone()

        return {
            "stores_cnt": stores_cnt,
            "prod_cnt": prod_cnt,
            "inv_cnt": inv_cnt,
            "sales_cnt": sales_cnt,
            "min_date": min_date,
            "max_date": max_date,
        }
    finally:
        conn.close()


def verify_patterns():
    """Programmatically verifies engineered demo patterns in SQLite data."""
    conn = get_connection()
    patterns_out = {}
    try:
        cursor = conn.cursor()

        # MILK (P001): low stock + strong recent 7-day demand
        milk_recent_qty = cursor.execute(
            "SELECT SUM(quantity) FROM Sales WHERE product_id = 'P001' AND date >= '2026-08-30'"
        ).fetchone()[0]
        milk_total_stock = cursor.execute(
            "SELECT SUM(current_stock) FROM Inventory WHERE product_id = 'P001'"
        ).fetchone()[0]
        patterns_out["milk"] = {
            "recent_7d_units": milk_recent_qty,
            "total_stock": milk_total_stock,
        }

        # BREAD (P002): high stock + low demand
        bread_recent_qty = cursor.execute(
            "SELECT SUM(quantity) FROM Sales WHERE product_id = 'P002' AND date >= '2026-08-30'"
        ).fetchone()[0]
        bread_total_stock = cursor.execute(
            "SELECT SUM(current_stock) FROM Inventory WHERE product_id = 'P002'"
        ).fetchone()[0]
        patterns_out["bread"] = {
            "recent_7d_units": bread_recent_qty,
            "total_stock": bread_total_stock,
        }

        # SHAMPOO (P012): baseline (first 50d) vs recent (final 10d) daily average
        shampoo_base_qty = (
            cursor.execute(
                "SELECT SUM(quantity) FROM Sales WHERE product_id = 'P012' AND date < '2026-08-27'"
            ).fetchone()[0]
            or 0
        )
        shampoo_rec_qty = (
            cursor.execute(
                "SELECT SUM(quantity) FROM Sales WHERE product_id = 'P012' AND date >= '2026-08-27'"
            ).fetchone()[0]
            or 0
        )
        patterns_out["shampoo"] = {
            "baseline_daily_avg": round(
                shampoo_base_qty / 50.0, 2
            ),  # across 3 stores
            "recent_daily_avg": round(
                shampoo_rec_qty / 10.0, 2
            ),  # across 3 stores
        }

        # COFFEE (P006): baseline (first 55d) vs recent spike (final 5d) daily average
        coffee_base_qty = (
            cursor.execute(
                "SELECT SUM(quantity) FROM Sales WHERE product_id = 'P006' AND date < '2026-09-01'"
            ).fetchone()[0]
            or 0
        )
        coffee_spike_qty = (
            cursor.execute(
                "SELECT SUM(quantity) FROM Sales WHERE product_id = 'P006' AND date >= '2026-09-01'"
            ).fetchone()[0]
            or 0
        )
        patterns_out["coffee"] = {
            "baseline_daily_avg": round(
                coffee_base_qty / 55.0, 2
            ),  # across 3 stores
            "spike_daily_avg": round(
                coffee_spike_qty / 5.0, 2
            ),  # across 3 stores
        }

        # NOTEBOOK (P017): final 14-day sales total = 0, current stock > 0
        notebook_recent_sales = (
            cursor.execute(
                "SELECT SUM(quantity) FROM Sales WHERE product_id = 'P017' AND date >= '2026-08-23'"
            ).fetchone()[0]
            or 0
        )
        notebook_stock = cursor.execute(
            "SELECT SUM(current_stock) FROM Inventory WHERE product_id = 'P017'"
        ).fetchone()[0]
        patterns_out["notebook"] = {
            "final_14d_sales": notebook_recent_sales,
            "total_stock": notebook_stock,
        }

        # OUT-OF-STOCK PRODUCT (P015 in S002)
        oos_row = cursor.execute(
            "SELECT store_id, product_id, current_stock FROM Inventory WHERE current_stock = 0"
        ).fetchone()
        patterns_out["out_of_stock"] = (
            f"Product {oos_row['product_id']} in Store {oos_row['store_id']}"
            if oos_row
            else "None"
        )

        # ZERO RECENT SALES PRODUCT (P030): latest 7 days = 0
        zero_rec_qty = (
            cursor.execute(
                "SELECT SUM(quantity) FROM Sales WHERE product_id = 'P030' AND date >= '2026-08-30'"
            ).fetchone()[0]
            or 0
        )
        patterns_out["zero_recent_sales"] = {
            "product_id": "P030",
            "recent_7d_sales": zero_rec_qty,
        }

        return patterns_out
    finally:
        conn.close()


def main():
    set_seed(42)
    init_db()

    stores = get_stores()
    products = get_products()
    inventory = generate_inventory(stores, products)
    sales = generate_sales(stores, products)

    save_to_database(stores, products, inventory, sales)
    save_to_csv(stores, products, inventory, sales)

    val_res = validate_dataset()
    patterns = verify_patterns()

    print("\nStockSense AI Dataset Generated Successfully\n")
    print(f"Stores: {val_res['stores_cnt']}")
    print(f"Products: {val_res['prod_cnt']}")
    print(f"Inventory records: {val_res['inv_cnt']}")
    print(f"Sales records: {val_res['sales_cnt']}\n")
    print(
        f"Sales period:\n{val_res['min_date']} to {val_res['max_date']}\n"
    )
    print("Demo patterns:")
    print("Milk 1L      -> low stock + strong recent demand")
    print("Bread        -> high stock + low demand")
    print("Shampoo      -> recent demand drop")
    print("Coffee       -> recent demand spike")
    print("Notebook     -> no sales in final 14 days")
    print(f"P015 (S002)  -> zero current stock")
    print(f"P030         -> zero sales in final 7 days\n")


if __name__ == "__main__":
    main()
