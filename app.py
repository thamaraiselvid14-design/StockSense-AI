import os
import sys
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import streamlit as st

# Ensure project root is in sys.path for module imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import (
    get_categories,
    get_dashboard_kpis,
    get_database_counts,
    get_inventory_intelligence,
    get_revenue_trend,
    get_stores_list,
    get_top_products_by_revenue,
)

# Load environment variables without failing if GEMINI_API_KEY is missing
load_dotenv()


def render_dashboard_page(db_metrics):
    kpis = get_dashboard_kpis()
    latest_date = kpis["latest_date"]

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center;">
                <h1 style="margin: 0; font-size: 2.25rem; font-weight: 800; color: #F8FAFC;">StockSense AI</h1>
                <span class="phase-badge">Retail Management Dashboard</span>
            </div>
            <div style="background-color: #1E293B; color: #38BDF8; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #334155;">
                📅 Last data date: <strong>{latest_date or 'N/A'}</strong>
            </div>
        </div>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 24px;">
            Here's what needs attention today
        </p>
    """,
        unsafe_allow_html=True,
    )

    # 6 KPI Cards in 2 rows of 3 columns
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    r2_c1, r2_c2, r2_c3 = st.columns(3)

    formatted_rev = f"₹{kpis['todays_revenue']:,.2f}" if kpis["latest_date"] else "—"
    formatted_units = f"{kpis['todays_units']:,}" if kpis["latest_date"] else "—"
    formatted_risk = f"{kpis['low_stock_count']}" if kpis["latest_date"] else "—"

    with r1_c1:
        st.markdown(
            f"""
            <div class="kpi-card blue-accent">
                <div class="kpi-label">Today's Revenue</div>
                <div class="kpi-value">{formatted_rev}</div>
                <div class="kpi-subtitle">For {latest_date or 'latest date'}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with r1_c2:
        st.markdown(
            f"""
            <div class="kpi-card blue-accent">
                <div class="kpi-label">Today's Units Sold</div>
                <div class="kpi-value">{formatted_units}</div>
                <div class="kpi-subtitle">For {latest_date or 'latest date'}</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with r1_c3:
        st.markdown(
            f"""
            <div class="kpi-card risk-accent">
                <div class="kpi-label">Products at Stock-out Risk</div>
                <div class="kpi-value">{formatted_risk}</div>
                <div class="kpi-subtitle">Temporary: below reorder level</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with r2_c1:
        st.markdown(
            """
            <div class="kpi-card amber-accent">
                <div class="kpi-label">Overstocked Products</div>
                <div class="kpi-value">—</div>
                <div class="kpi-subtitle">Phase 3 detection</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with r2_c2:
        st.markdown(
            """
            <div class="kpi-card amber-accent">
                <div class="kpi-label">Slow-moving Products</div>
                <div class="kpi-value">—</div>
                <div class="kpi-subtitle">Phase 3 detection</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with r2_c3:
        st.markdown(
            """
            <div class="kpi-card amber-accent">
                <div class="kpi-label">Sales Anomalies</div>
                <div class="kpi-value">—</div>
                <div class="kpi-subtitle">Phase 3 detection</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row: Revenue Trend (Left) & Top Products (Right)
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Revenue Trend — Last 30 Days")
        trend_data = get_revenue_trend(days=30)
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            fig_trend = px.line(
                df_trend,
                x="date",
                y="revenue",
                labels={"date": "Date", "revenue": "Revenue (₹)"},
                title=None,
            )
            fig_trend.update_traces(
                line=dict(color="#38BDF8", width=3),
                hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> ₹%{y:,.2f}<extra></extra>",
            )
            fig_trend.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#F8FAFC"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=340,
                xaxis=dict(showgrid=False, color="#94A3B8"),
                yaxis=dict(showgrid=True, gridcolor="#1F2937", color="#94A3B8"),
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No revenue trend data available.")

    with col_right:
        st.subheader("Top Products by Revenue (Last 30 Days)")
        top_products = get_top_products_by_revenue(days=30, limit=10)
        if top_products:
            df_top = pd.DataFrame(top_products)
            df_top_sorted = df_top.sort_values(by="total_revenue", ascending=True)
            fig_top = px.bar(
                df_top_sorted,
                x="total_revenue",
                y="product_name",
                orientation="h",
                labels={"total_revenue": "Revenue (₹)", "product_name": "Product"},
                title=None,
            )
            fig_top.update_traces(
                marker_color="#818CF8",
                hovertemplate="<b>Product:</b> %{y}<br><b>Revenue:</b> ₹%{x:,.2f}<extra></extra>",
            )
            fig_top.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#F8FAFC"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=340,
                xaxis=dict(showgrid=True, gridcolor="#1F2937", color="#94A3B8"),
                yaxis=dict(showgrid=False, color="#94A3B8"),
            )
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("No top product data available.")


def render_inventory_intelligence_page():
    st.markdown(
        """
        <h1 style="font-size: 2rem; font-weight: 800; color: #F8FAFC; margin-bottom: 4px;">Inventory Intelligence</h1>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 24px;">
            Monitor stock levels and recent sales velocity across stores.
        </p>
    """,
        unsafe_allow_html=True,
    )

    inv_records = get_inventory_intelligence(days=7)
    if not inv_records:
        st.warning("No inventory records match the query.")
        return

    df = pd.DataFrame(inv_records)

    # Filter controls
    col_f1, col_f2, col_f3 = st.columns(3)

    stores_data = get_stores_list()
    store_options = ["All Stores"] + [
        f"{s['store_name']} ({s['location']})" for s in stores_data
    ]
    store_map = {
        f"{s['store_name']} ({s['location']})": s["store_id"] for s in stores_data
    }

    categories = ["All Categories"] + get_categories()

    with col_f1:
        selected_store_name = st.selectbox("Store Filter", store_options, index=0)

    with col_f2:
        selected_category = st.selectbox("Category Filter", categories, index=0)

    with col_f3:
        search_term = st.text_input("Product Search", placeholder="Type product name...")

    # Apply filters locally on DataFrame
    if selected_store_name != "All Stores":
        target_store_id = store_map[selected_store_name]
        df = df[df["store_id"] == target_store_id]

    if selected_category != "All Categories":
        df = df[df["category"] == selected_category]

    if search_term and search_term.strip():
        df = df[
            df["product_name"].str.contains(search_term.strip(), case=False, na=False)
        ]

    if df.empty:
        st.info("No inventory records match the selected filters.")
        return

    # Process display table columns
    display_rows = []
    for _, row in df.iterrows():
        recent_units = int(row["recent_7d_units"])
        avg_daily = float(row["avg_daily_sales"])
        current_stock = int(row["current_stock"])

        if recent_units > 0 and avg_daily > 0:
            avg_daily_str = f"{avg_daily:.2f}"
            days_rem_val = current_stock / avg_daily
            days_rem_str = f"{days_rem_val:.1f}"
        else:
            avg_daily_str = "N/A"
            days_rem_str = "N/A"

        display_rows.append(
            {
                "Product": row["product_name"],
                "Category": row["category"],
                "Store": f"{row['store_name']} ({row['location']})",
                "Current Stock": current_stock,
                "7-Day Units": recent_units,
                "Average Daily Sales": avg_daily_str,
                "Days Remaining": days_rem_str,
                "Risk": "TBD",
                "Recommended Action": "TBD",
            }
        )

    df_display = pd.DataFrame(display_rows)

    st.markdown(
        f"<div style='margin-bottom: 12px; color: #94A3B8; font-size: 0.9rem;'>Showing <strong>{len(df_display)}</strong> inventory positions</div>",
        unsafe_allow_html=True,
    )

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Product": st.column_config.TextColumn("Product", width="medium"),
            "Category": st.column_config.TextColumn("Category", width="small"),
            "Store": st.column_config.TextColumn("Store", width="medium"),
            "Current Stock": st.column_config.NumberColumn("Current Stock", format="%d"),
            "7-Day Units": st.column_config.NumberColumn("7-Day Units", format="%d"),
            "Average Daily Sales": st.column_config.TextColumn("Average Daily Sales"),
            "Days Remaining": st.column_config.TextColumn("Days Remaining"),
            "Risk": st.column_config.TextColumn("Risk"),
            "Recommended Action": st.column_config.TextColumn("Recommended Action"),
        },
    )


def render_sales_analytics_stub():
    st.markdown(
        """
        <h1 style="font-size: 2rem; font-weight: 800; color: #F8FAFC; margin-bottom: 8px;">Sales Analytics</h1>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 24px;">
            Detailed sales trends and product performance are coming in Phase 3.
        </p>
        <div class="empty-state">
            📊 Sales Analytics features (store breakdown, category trends, peak hours) will be unlocked in Phase 3.
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_ai_copilot_stub():
    st.markdown(
        """
        <h1 style="font-size: 2rem; font-weight: 800; color: #F8FAFC; margin-bottom: 8px;">AI Copilot</h1>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 24px;">
            Ask questions about your sales and inventory data.
        </p>
    """,
        unsafe_allow_html=True,
    )

    st.text_input(
        "Ask a question about your inventory or sales:",
        placeholder="What products are running out?",
        disabled=True,
        key="copilot_input_stub",
    )

    st.markdown(
        """
        <div style="margin-top: 8px;">
            <span style="color: #64748B; font-size: 0.85rem; margin-right: 8px;">Example questions:</span>
            <span class="question-pill">What products are running out?</span>
            <span class="question-pill">What is overstocked?</span>
            <span class="question-pill">How did Milk perform this month?</span>
        </div>
        <div style="margin-top: 16px; color: #94A3B8; font-size: 0.9rem; font-style: italic;">
            🤖 AI Copilot will be activated in a later phase.
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_product_details_stub():
    st.markdown(
        """
        <h1 style="font-size: 2rem; font-weight: 800; color: #F8FAFC; margin-bottom: 8px;">Product Details</h1>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 24px;">
            Detailed product performance and inventory history.
        </p>
        <div class="empty-state">
            📦 Product Details view (individual product velocity, reorder calculation, historical demand graph) coming soon.
        </div>
    """,
        unsafe_allow_html=True,
    )


def render_app():
    st.set_page_config(
        page_title="StockSense AI - Retail Intelligence Copilot",
        page_icon="📦",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom styling for dark-themed analytics dashboard
    st.markdown(
        """
    <style>
    /* Main Background & Base Styling */
    .stApp {
        background-color: #0B0F17;
        color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1F2937;
    }
    
    /* Phase Indicator Badge */
    .phase-badge {
        display: inline-block;
        background-color: rgba(78, 161, 255, 0.15);
        color: #4EA1FF;
        border: 1px solid rgba(78, 161, 255, 0.3);
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 12px;
        vertical-align: middle;
    }
    
    /* KPI Card Styling */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: left;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: border-color 0.2s;
        margin-bottom: 12px;
    }
    .kpi-card:hover {
        border-color: #374151;
    }
    .kpi-card.blue-accent {
        border-left: 4px solid #38BDF8;
    }
    .kpi-card.risk-accent {
        border-left: 4px solid #EF4444;
    }
    .kpi-card.amber-accent {
        border-left: 4px solid #F59E0B;
    }
    .kpi-label {
        font-size: 0.825rem;
        color: #94A3B8;
        font-weight: 500;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 4px;
    }
    .kpi-subtitle {
        font-size: 0.75rem;
        color: #64748B;
    }

    /* Empty State Box */
    .empty-state {
        background-color: #111827;
        border: 1px dashed #334155;
        border-radius: 10px;
        padding: 36px;
        text-align: center;
        color: #94A3B8;
        font-size: 0.95rem;
    }
    
    /* Question Pill Badges */
    .question-pill {
        display: inline-block;
        background-color: #1E293B;
        color: #94A3B8;
        border: 1px solid #334155;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 4px 4px 4px 0;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    db_metrics = get_database_counts()

    # Sidebar Navigation & Branding
    with st.sidebar:
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=60)

        st.title("StockSense AI")
        st.caption("Retail Intelligence Copilot")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Inventory Intelligence",
                "Sales Analytics",
                "AI Copilot",
                "Product Details",
            ],
            index=0,
            key="navigation_radio",
        )

        st.markdown("---")
        if db_metrics["connected"]:
            st.markdown(
                f"""
                <div style="background-color: #1F2937; padding: 12px; border-radius: 8px; border: 1px solid #374151;">
                    <div style="color: #10B981; font-weight: 600; font-size: 0.85rem; margin-bottom: 8px;">
                        ● SQLite database connected
                    </div>
                    <div style="color: #94A3B8; font-size: 0.8rem; line-height: 1.6;">
                        <strong>Products:</strong> {db_metrics['products']}<br>
                        <strong>Stores:</strong> {db_metrics['stores']}<br>
                        <strong>Inventory:</strong> {db_metrics['inventory']}<br>
                        <strong>Sales Records:</strong> {db_metrics['sales']:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="background-color: #1F2937; padding: 12px; border-radius: 8px; border: 1px solid #EF4444;">
                    <div style="color: #EF4444; font-weight: 600; font-size: 0.85rem;">
                        ● SQLite database unavailable
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Page Router
    if page == "Dashboard":
        render_dashboard_page(db_metrics)
    elif page == "Inventory Intelligence":
        render_inventory_intelligence_page()
    elif page == "Sales Analytics":
        render_sales_analytics_stub()
    elif page == "AI Copilot":
        render_ai_copilot_stub()
    elif page == "Product Details":
        render_product_details_stub()


if __name__ == "__main__":
    if st.runtime.exists():
        render_app()
    else:
        import streamlit.web.cli as stcli

        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
