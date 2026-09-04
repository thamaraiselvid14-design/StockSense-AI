import os
import sys
from dotenv import load_dotenv
import streamlit as st

# Load environment variables without failing if GEMINI_API_KEY is missing
load_dotenv()


def render_dashboard():
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
    
    /* KPI Placeholder Card */
    .kpi-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 10px;
        padding: 20px;
        text-align: left;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: border-color 0.2s;
    }
    .kpi-card:hover {
        border-color: #374151;
    }
    .kpi-label {
        font-size: 0.875rem;
        color: #94A3B8;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.875rem;
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
        padding: 32px;
        text-align: center;
        color: #94A3B8;
        font-size: 0.95rem;
    }
    
    /* Chart Placeholder Box */
    .chart-placeholder {
        background-color: #111827;
        border: 1px dashed #334155;
        border-radius: 10px;
        height: 220px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #94A3B8;
        font-size: 0.9rem;
        text-align: center;
        padding: 20px;
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
            ["Dashboard", "AI Copilot", "Inventory", "Sales Analytics", "Alerts"],
            index=0,
        )

    # Page Router
    if page != "Dashboard":
        st.header(page)
        st.info("Coming in a later phase.")
        return

    # Main Header
    st.markdown(
        """
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <h1 style="margin: 0; font-size: 2.25rem; font-weight: 800; color: #F8FAFC;">StockSense AI</h1>
            <span class="phase-badge">Prototype foundation</span>
        </div>
        <p style="color: #94A3B8; font-size: 1.05rem; margin-top: 0; margin-bottom: 28px;">
            Here's what needs attention today
        </p>
    """,
        unsafe_allow_html=True,
    )

    # KPI Placeholder Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Today's Revenue</div>
                <div class="kpi-value">—</div>
                <div class="kpi-subtitle">Data not loaded</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Units Sold</div>
                <div class="kpi-value">—</div>
                <div class="kpi-subtitle">Data not loaded</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Low Stock Products</div>
                <div class="kpi-value">—</div>
                <div class="kpi-subtitle">Data not loaded</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
            <div class="kpi-card">
                <div class="kpi-label">Critical Alerts</div>
                <div class="kpi-value">—</div>
                <div class="kpi-subtitle">Data not loaded</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Today's Priorities Section
    st.subheader("Today's Priorities")
    st.markdown(
        """
        <div class="empty-state">
            No retail data loaded yet. Insights will appear after Phase 1.
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart Placeholders Section
    c_left, c_right = st.columns(2)

    with c_left:
        st.subheader("Revenue Trend")
        st.markdown(
            """
            <div class="chart-placeholder">
                Revenue data will appear after dataset initialization.
            </div>
        """,
            unsafe_allow_html=True,
        )

    with c_right:
        st.subheader("Inventory Health")
        st.markdown(
            """
            <div class="chart-placeholder">
                Inventory health analytics will appear after Phase 1.
            </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # AI Copilot Placeholder Section
    st.subheader("Ask StockSense")
    st.text_input(
        "Ask a question about your inventory or sales:",
        placeholder="What needs attention today?",
        disabled=True,
        key="copilot_input",
    )

    st.markdown(
        """
        <div style="margin-top: 8px;">
            <span style="color: #64748B; font-size: 0.85rem; margin-right: 8px;">Example questions:</span>
            <span class="question-pill">What products are running out?</span>
            <span class="question-pill">What is overstocked?</span>
            <span class="question-pill">How did Milk perform this month?</span>
        </div>
        <div style="margin-top: 12px; color: #94A3B8; font-size: 0.85rem; font-style: italic;">
            AI Copilot will be activated in a later phase.
        </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    if st.runtime.exists():
        render_dashboard()
    else:
        import streamlit.web.cli as stcli

        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
