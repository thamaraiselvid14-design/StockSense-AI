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

from backend.anomaly_engine import detect_sales_spike_or_drop, get_all_anomalies
from backend.database import (
    get_all_products_list,
    get_categories,
    get_dashboard_kpis,
    get_database_counts,
    get_product_daily_sales_history,
    get_product_info,
    get_product_inventory,
    get_revenue_trend,
    get_store_sales_comparison,
    get_stores_list,
    get_top_products_by_revenue,
)
from backend.inventory_engine import (
    calculate_avg_daily_sales,
    calculate_days_remaining,
    classify_stockout_risk,
    detect_overstock,
    detect_slow_moving,
    get_inventory_report,
)
from backend.sales_engine import (
    compare_stores,
    get_category_performance,
    get_product_performance,
    get_top_products,
)
from backend.recommendation_engine import recommend_action
from backend.gemini_service import (
    extract_intent,
    generate_grounded_explanation,
    is_gemini_available,
    validate_numeric_safety,
)
from backend.query_router import route_query


def get_deterministic_product_recommendation(
    stockout_risk, overstock_flag, movement_status, anomaly_status, days_remaining=None, current_stock=None
):
    """Delegates recommendation mapping to backend.recommendation_engine."""
    return recommend_action(
        {
            "stockout_risk": stockout_risk,
            "overstock_flag": overstock_flag,
            "movement_status": movement_status,
            "anomaly_status": anomaly_status,
            "days_remaining": days_remaining,
            "current_stock": current_stock,
        }
    )


def generate_priority_alerts(report_df, anomalies_df, limit=10):
    """Generates a prioritized list of evidence-backed alert dicts combining inventory and sales anomaly signals."""
    alerts = []
    seen_keys = set()

    # Process Inventory Alerts
    if not report_df.empty:
        for _, r in report_df.iterrows():
            prod_id = r["product_id"]
            store_id = r["store_id"]
            product_name = r["product"]
            store_name = r["store"]
            days_rem = r["days_remaining"]
            risk = r["stockout_risk"]
            overstock = r["overstock_flag"]
            movement = r["movement_status"]

            key = (prod_id, store_id)

            if risk == "OUT_OF_STOCK":
                seen_keys.add(key)
                alerts.append(
                    {
                        "priority": 1,
                        "badge_color": "#EF4444",
                        "message": f"🔴 <strong>{product_name}</strong> — {store_name} — currently out of stock",
                    }
                )
            elif risk == "CRITICAL":
                seen_keys.add(key)
                days_str = f"{days_rem:.1f}" if pd.notna(days_rem) else "N/A"
                alerts.append(
                    {
                        "priority": 2,
                        "badge_color": "#EF4444",
                        "message": f"🔴 <strong>{product_name}</strong> — {store_name} — likely stock-out in <strong>{days_str} days</strong>",
                    }
                )
            elif risk == "HIGH":
                seen_keys.add(key)
                days_str = f"{days_rem:.1f}" if pd.notna(days_rem) else "N/A"
                alerts.append(
                    {
                        "priority": 3,
                        "badge_color": "#F59E0B",
                        "message": f"🔴 <strong>{product_name}</strong> — {store_name} — likely stock-out in <strong>{days_str} days</strong>",
                    }
                )
            elif overstock == "OVERSTOCK_RISK":
                seen_keys.add(key)
                days_str = f"{days_rem:.1f}" if pd.notna(days_rem) else "N/A"
                alerts.append(
                    {
                        "priority": 6,
                        "badge_color": "#F59E0B",
                        "message": f"🟠 <strong>{product_name}</strong> — {store_name} — approximately <strong>{days_str} days</strong> of stock remaining",
                    }
                )
            elif movement == "NON_MOVING":
                seen_keys.add(key)
                alerts.append(
                    {
                        "priority": 7,
                        "badge_color": "#EAB308",
                        "message": f"🟡 <strong>{product_name}</strong> — {store_name} — no sales recorded in the last 14 days",
                    }
                )
            elif movement == "SLOW_MOVING":
                seen_keys.add(key)
                alerts.append(
                    {
                        "priority": 8,
                        "badge_color": "#EAB308",
                        "message": f"🟡 <strong>{product_name}</strong> — {store_name} — recent sales fell below 30% of the previous week's rate",
                    }
                )

    # Process Sales Anomaly Alerts at Product Level
    if not anomalies_df.empty:
        for _, a in anomalies_df.iterrows():
            prod_id = a["product_id"]
            prod_name = a["product"]
            pct = a["percent_change"]
            status = a["status"]

            if status == "SPIKE" and pd.notna(pct):
                alerts.append(
                    {
                        "priority": 5,
                        "badge_color": "#10B981",
                        "message": f"🟢 <strong>{prod_name}</strong> — sales up <strong>+{pct:.1f}%</strong> versus baseline",
                    }
                )
            elif status == "DROP" and pd.notna(pct):
                alerts.append(
                    {
                        "priority": 4,
                        "badge_color": "#EAB308",
                        "message": f"🟡 <strong>{prod_name}</strong> — sales down <strong>{pct:.1f}%</strong> versus baseline",
                    }
                )

    # Sort alerts by priority score ascending
    alerts.sort(key=lambda x: x["priority"])
    return alerts[:limit]


def render_dashboard_page(db_metrics):
    kpis = get_dashboard_kpis()
    latest_date = kpis["latest_date"]

    inventory_df = get_inventory_report()
    anomalies_df = get_all_anomalies()

    if not inventory_df.empty:
        stockout_risk_count = len(
            inventory_df[
                inventory_df["stockout_risk"].isin(
                    ["OUT_OF_STOCK", "CRITICAL", "HIGH"]
                )
            ]
        )
        overstock_count = len(
            inventory_df[inventory_df["overstock_flag"] == "OVERSTOCK_RISK"]
        )
        slow_moving_count = len(
            inventory_df[
                inventory_df["movement_status"].isin(
                    ["SLOW_MOVING", "NON_MOVING"]
                )
            ]
        )
    else:
        stockout_risk_count = 0
        overstock_count = 0
        slow_moving_count = 0

    anomaly_count = len(anomalies_df) if not anomalies_df.empty else 0

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

    # 6 Real KPI Cards in 2 rows of 3 columns
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    r2_c1, r2_c2, r2_c3 = st.columns(3)

    formatted_rev = f"₹{kpis['todays_revenue']:,.2f}" if latest_date else "—"
    formatted_units = f"{kpis['todays_units']:,}" if latest_date else "—"

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
                <div class="kpi-value">{stockout_risk_count}</div>
                <div class="kpi-subtitle">Out of stock / Critical / High</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with r2_c1:
        st.markdown(
            f"""
            <div class="kpi-card amber-accent">
                <div class="kpi-label">Overstocked Products</div>
                <div class="kpi-value">{overstock_count}</div>
                <div class="kpi-subtitle">Above 30 days supply</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with r2_c2:
        st.markdown(
            f"""
            <div class="kpi-card amber-accent">
                <div class="kpi-label">Slow-moving Products</div>
                <div class="kpi-value">{slow_moving_count}</div>
                <div class="kpi-subtitle">Low or zero recent velocity</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with r2_c3:
        st.markdown(
            f"""
            <div class="kpi-card amber-accent">
                <div class="kpi-label">Sales Anomalies</div>
                <div class="kpi-value">{anomaly_count}</div>
                <div class="kpi-subtitle">Spikes / Drops detected</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Today's Priority Alerts Section
    st.subheader("Today's Priority Alerts")
    priority_alerts = generate_priority_alerts(inventory_df, anomalies_df, limit=10)

    if priority_alerts:
        alert_html_items = ""
        for alert in priority_alerts:
            alert_html_items += f"""
            <div style="background-color: #111827; border: 1px solid #1F2937; border-left: 4px solid {alert['badge_color']}; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; font-size: 0.95rem; color: #F8FAFC;">
                {alert['message']}
            </div>
            """
        st.markdown(
            f"""
            <div style="margin-bottom: 24px;">
                {alert_html_items}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="empty-state" style="margin-bottom: 24px;">
                🟢 All inventory levels and demand trends are normal. No priority alerts detected today.
            </div>
        """,
            unsafe_allow_html=True,
        )

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

    inventory_df = get_inventory_report()
    if inventory_df.empty:
        st.warning("No inventory records available.")
        return

    df = inventory_df.copy()

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
            df["product"].str.contains(search_term.strip(), case=False, na=False)
        ]

    if df.empty:
        st.info("No inventory records match the selected filters.")
        return

    # Process display table columns
    display_rows = []
    for _, row in df.iterrows():
        avg_daily = row["avg_daily_sales"]
        days_rem = row["days_remaining"]
        stock = int(row["current_stock"])

        if pd.notna(avg_daily) and avg_daily is not None:
            avg_daily_str = f"{avg_daily:.2f}"
        else:
            avg_daily_str = "N/A"

        if stock == 0:
            days_rem_str = "0.0"
        elif pd.notna(days_rem) and days_rem is not None:
            days_rem_str = f"{days_rem:.1f}"
        else:
            days_rem_str = "N/A"

        display_rows.append(
            {
                "Product": row["product"],
                "Category": row["category"],
                "Store": row["store"],
                "Current Stock": stock,
                "Average Daily Sales": avg_daily_str,
                "Days Remaining": days_rem_str,
                "Risk": row["stockout_risk"],
                "Overstock": row["overstock_flag"],
                "Movement": row["movement_status"],
                "Recommended Action": row["recommended_action"],
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
            "Average Daily Sales": st.column_config.TextColumn("Average Daily Sales"),
            "Days Remaining": st.column_config.TextColumn("Days Remaining"),
            "Risk": st.column_config.TextColumn("Risk"),
            "Overstock": st.column_config.TextColumn("Overstock"),
            "Movement": st.column_config.TextColumn("Movement"),
            "Recommended Action": st.column_config.TextColumn("Recommended Action"),
        },
    )


def render_sales_analytics_page():
    st.markdown(
        """
        <h1 style="font-size: 2rem; font-weight: 800; color: #F8FAFC; margin-bottom: 4px;">Sales Analytics</h1>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 24px;">
            Understand revenue trends, product performance and unusual demand changes.
        </p>
    """,
        unsafe_allow_html=True,
    )

    # Filter controls
    c1, c2, c3 = st.columns(3)

    stores_data = get_stores_list()
    store_options = ["All Stores"] + [
        f"{s['store_name']} ({s['location']})" for s in stores_data
    ]
    store_map = {
        f"{s['store_name']} ({s['location']})": s["store_id"] for s in stores_data
    }

    products_data = get_all_products_list()
    product_options = [f"{p['product_name']} ({p['product_id']})" for p in products_data]
    prod_map = {f"{p['product_name']} ({p['product_id']})": p["product_id"] for p in products_data}

    with c1:
        sel_store = st.selectbox("Store Filter", store_options, index=0, key="sa_store")
    with c2:
        sel_prod = st.selectbox("Product Drilldown", product_options, index=0, key="sa_prod")
    with c3:
        sel_period = st.selectbox("Analysis Period", [7, 14, 30], index=2, key="sa_period")

    store_id = store_map[sel_store] if sel_store != "All Stores" else None
    product_id = prod_map[sel_prod]

    # Revenue Trend Section
    st.subheader(f"Daily Revenue Trend ({sel_period} Days)")
    trend_data = get_revenue_trend(days=sel_period, store_id=store_id)
    if trend_data:
        df_tr = pd.DataFrame(trend_data)
        fig_tr = px.line(
            df_tr,
            x="date",
            y="revenue",
            labels={"date": "Date", "revenue": "Revenue (₹)"},
            title=None,
        )
        fig_tr.update_traces(
            line=dict(color="#38BDF8", width=3),
            hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> ₹%{y:,.2f}<extra></extra>",
        )
        fig_tr.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#F8FAFC"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            xaxis=dict(showgrid=False, color="#94A3B8"),
            yaxis=dict(showgrid=True, gridcolor="#1F2937", color="#94A3B8"),
        )
        st.plotly_chart(fig_tr, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Selected Product Performance Cards
    perf = get_product_performance(product_id, period_days=sel_period)
    st.subheader(f"Performance Overview: {perf['product_name']}")

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Units Sold", f"{perf['total_units_sold']:,}")
    with m2:
        st.metric("Total Revenue", f"₹{perf['total_revenue']:,.2f}")
    with m3:
        growth_str = (
            f"{perf['growth_percent']:+.1f}%"
            if perf["growth_percent"] is not None
            else "N/A"
        )
        st.metric("Revenue Growth", growth_str)
    with m4:
        st.metric("Current Stock", f"{perf['current_stock']}")
    with m5:
        best_store_str = (
            perf["best_performing_store"]["store_name"]
            if perf["best_performing_store"]
            else "N/A"
        )
        st.metric("Best Store", best_store_str)

    st.markdown("<br>", unsafe_allow_html=True)

    # Store Comparison & Category Performance Row
    sc_col, cat_col = st.columns([1, 1])

    with sc_col:
        st.subheader("Store Sales Comparison")
        comp_res = compare_stores(product_id, period_days=sel_period)
        df_comp = comp_res["df"]

        if not df_comp.empty:
            fig_comp = px.bar(
                df_comp,
                x="store",
                y="units_sold",
                labels={"store": "Store", "units_sold": "Units Sold"},
                color="units_sold",
                color_continuous_scale="Blues",
            )
            fig_comp.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#F8FAFC"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=280,
                coloraxis_showscale=False,
                xaxis=dict(showgrid=False, color="#94A3B8"),
                yaxis=dict(showgrid=True, gridcolor="#1F2937", color="#94A3B8"),
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            gap = comp_res["gap_between_top_two"]
            gap_str = f"<strong>{gap} units</strong>" if gap is not None else "N/A"
            st.markdown(
                f"<div style='color: #94A3B8; font-size: 0.85rem;'>Top-store lead gap: {gap_str}</div>",
                unsafe_allow_html=True,
            )

    with cat_col:
        st.subheader(f"Category Revenue Breakdown ({sel_period} Days)")
        cat_perf = get_category_performance(period_days=sel_period)
        if cat_perf:
            df_cat = pd.DataFrame(cat_perf).sort_values(
                by="revenue", ascending=True
            )
            fig_cat = px.bar(
                df_cat,
                x="revenue",
                y="category",
                orientation="h",
                labels={"revenue": "Revenue (₹)", "category": "Category"},
            )
            fig_cat.update_traces(
                marker_color="#38BDF8",
                hovertemplate="<b>Category:</b> %{y}<br><b>Revenue:</b> ₹%{x:,.2f}<extra></extra>",
            )
            fig_cat.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#F8FAFC"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=280,
                xaxis=dict(showgrid=True, gridcolor="#1F2937", color="#94A3B8"),
                yaxis=dict(showgrid=False, color="#94A3B8"),
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sales Anomaly Table Section
    st.subheader("Sales Anomaly Detection")
    st.caption("Products exhibiting unusual sales spikes (≥+50%) or drops (≤-40%) versus 21-day baseline")

    anom_df = get_all_anomalies()
    if not anom_df.empty:
        disp_anom = []
        for _, r in anom_df.iterrows():
            pct = r["percent_change"]
            pct_str = f"{pct:+.1f}%" if pd.notna(pct) else "N/A"
            disp_anom.append(
                {
                    "Product": r["product"],
                    "Category": r["category"],
                    "Status": r["status"],
                    "Recent 7-Day Avg": f"{r['recent_avg']:.2f} units/day",
                    "Baseline 21-Day Avg": f"{r['baseline_avg']:.2f} units/day",
                    "Percent Change": pct_str,
                }
            )
        st.dataframe(
            pd.DataFrame(disp_anom),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Product": st.column_config.TextColumn("Product", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Status": st.column_config.TextColumn("Status"),
                "Recent 7-Day Avg": st.column_config.TextColumn("Recent 7-Day Avg"),
                "Baseline 21-Day Avg": st.column_config.TextColumn("Baseline 21-Day Avg"),
                "Percent Change": st.column_config.TextColumn("Percent Change"),
            },
        )
    else:
        st.info("No sales anomalies detected for the current period.")


def render_product_details_page():
    st.markdown(
        """
        <h1 style="font-size: 2rem; font-weight: 800; color: #F8FAFC; margin-bottom: 4px;">Product Details</h1>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 24px;">
            Detailed product performance and inventory history.
        </p>
    """,
        unsafe_allow_html=True,
    )

    products_data = get_all_products_list()
    product_options = [f"{p['product_name']} ({p['product_id']})" for p in products_data]
    prod_map = {f"{p['product_name']} ({p['product_id']})": p["product_id"] for p in products_data}

    sel_prod_label = st.selectbox("Select Product", product_options, index=0, key="pd_select")
    product_id = prod_map[sel_prod_label]

    perf = get_product_performance(product_id, period_days=30)
    anom = detect_sales_spike_or_drop(product_id, store_id=None)

    # Product Header Info
    st.markdown(
        f"""
        <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div>
                    <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #F8FAFC;">{perf['product_name']}</h2>
                    <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">
                        Category: <strong>{perf['category']}</strong> | Product ID: <code>{perf['product_id']}</code>
                    </div>
                </div>
                <div style="display: flex; gap: 20px; font-size: 0.9rem; color: #94A3B8;">
                    <span>Unit Price: <strong style="color: #F8FAFC;">₹{perf['price']:,.2f}</strong></span>
                    <span>Reorder Level: <strong style="color: #F8FAFC;">{perf['reorder_level']} units</strong></span>
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Evaluate Overall Product Inventory & Risk
    inv_report = get_inventory_report()
    p_inv = inv_report[inv_report["product_id"] == product_id]

    if not p_inv.empty:
        total_stock = int(p_inv["current_stock"].sum())
        total_rec_units = int(p_inv["recent_7_units"].sum())
        avg_daily = (total_rec_units / 7.0) if total_rec_units > 0 else None
        days_rem = calculate_days_remaining(total_stock, avg_daily)
        stock_risk = classify_stockout_risk(days_rem)
        overstock = (
            "OVERSTOCK_RISK"
            if (days_rem is not None and days_rem > 30)
            else "NORMAL"
        )
        total_14 = int(p_inv["last_14_units"].sum())
        if total_14 == 0:
            movement = "NON_MOVING"
        else:
            prior_tot = int(p_inv["prior_7_units"].sum())
            if prior_tot > 0 and (total_rec_units / 7.0) < 0.30 * (prior_tot / 7.0):
                movement = "SLOW_MOVING"
            else:
                movement = "NORMAL"
    else:
        total_stock = 0
        avg_daily = None
        days_rem = None
        stock_risk = "UNKNOWN"
        overstock = "NORMAL"
        movement = "NORMAL"

    anom_status = anom["status"]

    # Deterministic Recommendation & Edge-Case Note Banners
    rec_text = get_deterministic_product_recommendation(
        stock_risk, overstock, movement, anom_status, days_rem
    )

    st.markdown(
        f"""
        <div style="background-color: #1E293B; border-left: 4px solid #38BDF8; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; color: #F8FAFC;">
            💡 <strong>Recommended Action:</strong> {rec_text}
        </div>
    """,
        unsafe_allow_html=True,
    )

    if total_stock == 0:
        st.markdown(
            """
            <div style="background-color: #451A03; border: 1px solid #78350F; border-radius: 8px; padding: 10px 14px; margin-bottom: 20px; color: #FDE68A; font-size: 0.875rem;">
                🔴 <strong>Stock Status:</strong> Product is currently out of stock.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif avg_daily is None and total_stock > 0:
        st.markdown(
            """
            <div style="background-color: #111827; border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; margin-bottom: 20px; color: #94A3B8; font-size: 0.875rem;">
                💡 <strong>Velocity Note:</strong> This product has recorded no recent sales, so a reliable stock-out estimate cannot be calculated.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 10 Metric Cards in 2 rows
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("30-Day Units Sold", f"{perf['total_units_sold']:,}")
    with c2:
        st.metric("30-Day Revenue", f"₹{perf['total_revenue']:,.2f}")
    with c3:
        g_str = (
            f"{perf['growth_percent']:+.1f}%"
            if perf["growth_percent"] is not None
            else "N/A"
        )
        st.metric("Revenue Growth", g_str)
    with c4:
        st.metric("Current Inventory", f"{total_stock} units")
    with c5:
        avg_str = f"{avg_daily:.2f}" if avg_daily is not None else "N/A"
        st.metric("Avg Daily Sales", avg_str)

    c6, c7, c8, c9, c10 = st.columns(5)
    with c6:
        d_str = f"{days_rem:.1f}" if days_rem is not None else "N/A"
        st.metric("Days Remaining", d_str)
    with c7:
        st.metric("Stockout Risk", stock_risk)
    with c8:
        st.metric("Overstock Status", overstock)
    with c9:
        st.metric("Movement Status", movement)
    with c10:
        st.metric("Sales Anomaly", anom_status)

    st.markdown("<br>", unsafe_allow_html=True)

    # Daily Sales History Chart & Store Inventory Table
    ch_col, tbl_col = st.columns([3, 2])

    with ch_col:
        st.subheader("30-Day Sales History")
        history = get_product_daily_sales_history(product_id, days=30)
        if history:
            df_hist = pd.DataFrame(history)
            fig_hist = px.line(
                df_hist,
                x="date",
                y="units_sold",
                labels={"date": "Date", "units_sold": "Units Sold"},
            )
            fig_hist.update_traces(
                line=dict(color="#818CF8", width=3),
                hovertemplate="<b>Date:</b> %{x}<br><b>Units Sold:</b> %{y}<extra></extra>",
            )
            fig_hist.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#F8FAFC"),
                margin=dict(l=20, r=20, t=20, b=20),
                height=300,
                xaxis=dict(showgrid=False, color="#94A3B8"),
                yaxis=dict(showgrid=True, gridcolor="#1F2937", color="#94A3B8"),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    with tbl_col:
        st.subheader("Inventory Position by Store")
        if not p_inv.empty:
            store_rows = []
            for _, sr in p_inv.iterrows():
                st_stock = int(sr["current_stock"])
                st_avg = sr["avg_daily_sales"]
                st_days = sr["days_remaining"]

                st_avg_str = f"{st_avg:.2f}" if pd.notna(st_avg) and st_avg is not None else "N/A"
                if st_stock == 0:
                    st_days_str = "0.0"
                elif pd.notna(st_days) and st_days is not None:
                    st_days_str = f"{st_days:.1f}"
                else:
                    st_days_str = "N/A"

                store_rows.append(
                    {
                        "Store": sr["store"],
                        "Stock": st_stock,
                        "Avg Sales": st_avg_str,
                        "Days Rem": st_days_str,
                        "Risk": sr["stockout_risk"],
                    }
                )

            st.dataframe(
                pd.DataFrame(store_rows),
                use_container_width=True,
                hide_index=True,
            )


def render_ai_copilot_page():
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap;">
            <h1 style="font-size: 2rem; font-weight: 800; color: #F8FAFC; margin: 0;">AI Retail Copilot</h1>
        </div>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 20px;">
            Ask natural-language questions about stockouts, overstock, sales velocity, anomalies, and store performance.
        </p>
    """,
        unsafe_allow_html=True,
    )

    # Gemini API Availability status banner
    if is_gemini_available():
        st.markdown(
            """
            <div style="background-color: #064E3B; border: 1px solid #059669; color: #6EE7B7; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; margin-bottom: 20px;">
                🟢 <strong>Gemini AI Active</strong> (Evaluator Model: <code>gemini-3.5-flash-lite</code>) — Natural language intent extraction & grounded explanation enabled.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background-color: #1E293B; border: 1px solid #334155; color: #38BDF8; padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; margin-bottom: 20px;">
                🤖 <strong>AI Copilot is temporarily unavailable — showing deterministic dashboard data instead</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Sample Questions Section
    st.markdown(
        "<div style='color: #94A3B8; font-size: 0.9rem; font-weight: 600; margin-bottom: 8px;'>Sample Questions:</div>",
        unsafe_allow_html=True,
    )
    sample_cols = st.columns(4)

    samples = [
        "What products are running out of stock?",
        "What inventory is overstocked?",
        "Which products are slow-moving?",
        "Show sales spikes and drops",
        "How did Milk perform this month?",
        "Which store sells the most Bread?",
        "Summarize overall business performance today",
        "What is the status of Eggs?",
    ]

    if "copilot_query" not in st.session_state:
        st.session_state["copilot_query"] = ""

    for idx, s_text in enumerate(samples):
        col_target = sample_cols[idx % 4]
        with col_target:
            if st.button(s_text, key=f"sample_btn_{idx}", use_container_width=True):
                st.session_state["copilot_query"] = s_text
                st.rerun()

    # Query Input Field
    user_query = st.text_input(
        "Ask a question about inventory, sales, or store operations:",
        value=st.session_state["copilot_query"],
        placeholder="e.g., What products are at stockout risk?",
        key="copilot_input_field",
    )

    if user_query and user_query.strip():
        with st.spinner("Analyzing question with Python Deterministic Engines & Gemini..."):
            # Step 1: Extract Intent
            intent_data = extract_intent(user_query.strip())

            # Step 2: Route Query to Deterministic Engines
            payload = route_query(intent_data)

            # Step 3: Generate Grounded Explanation
            explanation = generate_grounded_explanation(user_query.strip(), intent_data, payload)

            # Step 4: Numeric Safety Validation
            safety_res = validate_numeric_safety(explanation, payload)

        # Display Pipeline Intent Badge & Target Parameters
        extracted_intent = intent_data.get("intent", "unsupported")
        extracted_prod = intent_data.get("product") or "All"
        extracted_store = intent_data.get("store") or "All"

        st.markdown(
            f"""
            <div style="background-color: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 12px 16px; margin-top: 16px; margin-bottom: 16px;">
                <div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 0.85rem; color: #94A3B8;">
                    <span>Target Intent: <strong style="color: #38BDF8;">{extracted_intent}</strong></span>
                    <span>Product: <strong style="color: #F8FAFC;">{extracted_prod}</strong></span>
                    <span>Store: <strong style="color: #F8FAFC;">{extracted_store}</strong></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Canonical Recommendation Box
        rec_text = payload.get("recommended_action", "No action needed")
        rec_color = "#38BDF8"
        if rec_text in ["Replenish immediately", "Increase replenishment priority"]:
            rec_color = "#EF4444"
        elif rec_text in ["Reorder soon", "Reduce next order", "Investigate demand"]:
            rec_color = "#F59E0B"

        st.markdown(
            f"""
            <div style="background-color: #1E293B; border-left: 4px solid {rec_color}; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; color: #F8FAFC;">
                💡 <strong>Canonical Recommendation:</strong> <span style="font-size: 1.1rem; font-weight: 700; color: {rec_color};">{rec_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Grounded Explanation
        st.markdown(
            """
            <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;">
                🤖 AI Copilot Answer:
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(explanation)

        # Numeric Safety Badge
        if safety_res["is_safe"]:
            st.markdown(
                """
                <div style="background-color: #064E3B; color: #6EE7B7; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; display: inline-block; margin-top: 12px; margin-bottom: 20px;">
                    🛡️ <strong>Numeric Grounding Safety Verified:</strong> All numeric figures in this explanation match deterministic backend payload evidence.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            ungrounded_str = ", ".join(safety_res["ungrounded_numbers"])
            st.markdown(
                f"""
                <div style="background-color: #78350F; color: #FDE68A; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; display: inline-block; margin-top: 12px; margin-bottom: 20px;">
                    ⚠️ <strong>Numeric Safety Flag:</strong> Found unverified numeric values ({ungrounded_str}). Please cross-reference with payload below.
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Verified Evidence Payload Expander
        with st.expander("🔍 View Verified Evidence Payload (Deterministic Backend Facts)", expanded=False):
            st.json(payload)

            details = payload.get("details", [])
            if details and isinstance(details, list):
                st.markdown("#### Evidence Data Table")
                st.dataframe(pd.DataFrame(details), use_container_width=True, hide_index=True)


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
        render_sales_analytics_page()
    elif page == "AI Copilot":
        render_ai_copilot_page()
    elif page == "Product Details":
        render_product_details_page()


if __name__ == "__main__":
    if st.runtime.exists():
        render_app()
    else:
        import streamlit.web.cli as stcli

        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
