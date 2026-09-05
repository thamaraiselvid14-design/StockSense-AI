"""SQLite database connection, initialization, and query utilities for StockSense AI."""

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
