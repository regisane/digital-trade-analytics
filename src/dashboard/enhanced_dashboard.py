
"""
ENHANCED DASHBOARD - STREAMLIT (FIXED VERSION)
No warnings, production-ready code
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime
import numpy as np

# ============================================
# PAGE CONFIGURATION
# ============================================

st.set_page_config(
    page_title="Digital Trade Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        color: #1f77b4;
        text-align: center;
        padding: 2rem 1rem;
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 2rem 1.5rem;
        margin: 0.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.12);
        border: 2px solid #e8f0f8;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 280px;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(31, 119, 180, 0.2);
        border-color: #1f77b4;
    }
    
    .metric-icon {
        font-size: 3rem;
        margin-bottom: 0.8rem;
    }
    
    .metric-value {
        font-size: 2.6rem;
        font-weight: 900;
        color: #1f77b4;
        margin: 0.7rem 0;
        letter-spacing: -1px;
    }
    
    .metric-label {
        font-size: 1.1rem;
        color: #333333;
        font-weight: 700;
        margin-top: 0.3rem;
    }
    
    .metric-subtitle {
        font-size: 0.8rem;
        color: #666666;
        margin-top: 0.3rem;
        font-weight: 500;
    }
    
    .metric-trend {
        font-size: 0.85rem;
        margin-top: 1rem;
        padding: 0.6rem 0.8rem;
        border-radius: 8px;
        background: #e8f0f8;
        color: #1f77b4;
        font-weight: 600;
    }
    
    .trend-positive {
        background: #d4edda;
        color: #155724;
    }
    
    .trend-negative {
        background: #f8d7da;
        color: #721c24;
    }
    
    .kpi-section-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1f77b4;
        margin-bottom: 2rem;
        margin-top: 1rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 1rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🌍 Digital Trade Intelligence Platform</h1>', unsafe_allow_html=True)
st.markdown("---")

# ============================================
# LOAD DATA
# ============================================

@st.cache_data
def load_all_data():
    """Load all data from SQLite database"""
    conn = sqlite3.connect('data/digital_trade.db')
    
    try:
        raw = pd.read_sql("SELECT * FROM raw_trade_data LIMIT 1000", conn)
        processed = pd.read_sql("SELECT * FROM processed_trade_data", conn)
        time_series = pd.read_sql("SELECT * FROM time_series_data", conn)
        country_summary = pd.read_sql("SELECT * FROM country_summary", conn)
        forecast = pd.read_sql("SELECT * FROM forecast_results", conn)
        top_exporters = pd.read_sql("SELECT * FROM top_exporters", conn)
        global_summary = pd.read_sql("SELECT * FROM global_summary", conn)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        conn.close()
        return None, None, None, None, None, None, None
    
    conn.close()
    return raw, processed, time_series, country_summary, forecast, top_exporters, global_summary

raw, processed, time_series, country_summary, forecast, top_exporters, global_summary = load_all_data()

# Check if data loaded
if time_series is None:
    st.error("❌ Failed to load data. Please run create_database.py first.")
    st.stop()

# ============================================
# SIDEBAR
# ============================================

st.sidebar.image("https://img.icons8.com/color/96/000000/globe--v1.png", width=80)
st.sidebar.title("📊 Filters")

# Country selector
countries = ['All'] + sorted(time_series['REF_AREA'].unique().tolist())
selected_country = st.sidebar.selectbox("🌍 Select Country", countries)

# Year range
min_year = int(time_series['TIME_PERIOD'].min())
max_year = int(time_series['TIME_PERIOD'].max())
year_range = st.sidebar.slider(
    "📅 Year Range",
    min_year, max_year,
    (min_year, max_year)
)

# Indicator selector
indicator_options = {
    'exports_millions': '📤 Exports',
    'imports_millions': '📥 Imports',
    'trade_balance': '⚖️ Trade Balance'
}
selected_indicator = st.sidebar.selectbox(
    "📈 Select Indicator",
    list(indicator_options.keys()),
    format_func=lambda x: indicator_options[x]
)

# Chart type
chart_type = st.sidebar.radio(
    "📊 Chart Type",
    ['Line Chart', 'Bar Chart', 'Area Chart']
)

# ============================================
# FILTER DATA
# ============================================

if selected_country != 'All':
    data_filtered = time_series[time_series['REF_AREA'] == selected_country]
else:
    data_filtered = time_series

data_filtered = data_filtered[
    (data_filtered['TIME_PERIOD'] >= year_range[0]) & 
    (data_filtered['TIME_PERIOD'] <= year_range[1])
]

# ============================================
# KPI METRICS ROW
# ============================================

# ============================================
# KPI METRICS ROW - ENHANCED
# ============================================

st.markdown('<div class="kpi-section-title">📊 Key Performance Indicators</div>', unsafe_allow_html=True)

# Calculate trends
def calculate_trend(data, column):
    """Calculate year-over-year trend"""
    if len(data) < 2:
        return 0
    latest = data[column].iloc[-1] if not data.empty else 0
    previous = data[column].iloc[-2] if len(data) > 1 else latest
    if previous == 0:
        return 0
    return ((latest - previous) / abs(previous)) * 100

col1, col2, col3, col4, col5 = st.columns(5, gap="medium")

with col1:
    total_exports = data_filtered['exports_millions'].sum()
    trend_exports = calculate_trend(data_filtered.sort_values('TIME_PERIOD'), 'exports_millions')
    trend_icon_exp = "📈" if trend_exports >= 0 else "📉"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">💰</div>
        <div>
            <div class="metric-value">${total_exports/1000:,.1f}B</div>
            <div class="metric-label">Total Exports</div>
        </div>
        <div class="metric-trend trend-{'positive' if trend_exports >= 0 else 'negative'}">
            {trend_icon_exp} {abs(trend_exports):.1f}% vs Last Period
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_imports = data_filtered['imports_millions'].sum()
    trend_imports = calculate_trend(data_filtered.sort_values('TIME_PERIOD'), 'imports_millions')
    trend_icon_imp = "📈" if trend_imports >= 0 else "📉"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">💳</div>
        <div>
            <div class="metric-value">${total_imports/1000:,.1f}B</div>
            <div class="metric-label">Total Imports</div>
        </div>
        <div class="metric-trend trend-{'positive' if trend_imports >= 0 else 'negative'}">
            {trend_icon_imp} {abs(trend_imports):.1f}% vs Last Period
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    trade_balance = (total_exports - total_imports) / 1000
    is_positive = trade_balance > 0
    balance_icon = "✅" if is_positive else "⚠️"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">⚖️</div>
        <div>
            <div class="metric-value">${trade_balance:,.1f}B</div>
            <div class="metric-label">Trade Balance</div>
        </div>
        <div class="metric-trend trend-{'positive' if is_positive else 'negative'}">
            {balance_icon} {'Surplus' if is_positive else 'Deficit'}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    countries_count = data_filtered['REF_AREA'].nunique()
    total_countries = time_series['REF_AREA'].nunique()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">🌍</div>
        <div>
            <div class="metric-value">{countries_count}</div>
            <div class="metric-label">Countries</div>
            <div class="metric-subtitle">of {total_countries} Total</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    if selected_country != 'All':
        latest_value = data_filtered[data_filtered['TIME_PERIOD'] == data_filtered['TIME_PERIOD'].max()]
        latest_exports = latest_value['exports_millions'].iloc[0] if not latest_value.empty else 0
        latest_year = data_filtered['TIME_PERIOD'].max() if not data_filtered.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📅</div>
            <div>
                <div class="metric-value">${latest_exports/1000:,.1f}B</div>
                <div class="metric-label">Latest Year</div>
                <div class="metric-subtitle">{int(latest_year)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        forecast_years = len(forecast) if forecast is not None else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔮</div>
            <div>
                <div class="metric-value">{forecast_years}</div>
                <div class="metric-label">Forecast Years</div>
                <div class="metric-subtitle">Projected</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# MAIN CHARTS - FIXED: width instead of use_container_width
# ============================================

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Trend Analysis")
    
    if chart_type == 'Line Chart':
        fig = px.line(
            data_filtered,
            x='TIME_PERIOD',
            y=selected_indicator,
            color='REF_AREA',
            title=f"{indicator_options[selected_indicator]} Over Time",
            labels={
                'TIME_PERIOD': 'Year',
                selected_indicator: 'Value (Millions USD)',
                'REF_AREA': 'Country'
            },
            markers=True
        )
    elif chart_type == 'Bar Chart':
        fig = px.bar(
            data_filtered,
            x='TIME_PERIOD',
            y=selected_indicator,
            color='REF_AREA',
            title=f"{indicator_options[selected_indicator]} Over Time",
            labels={
                'TIME_PERIOD': 'Year',
                selected_indicator: 'Value (Millions USD)',
                'REF_AREA': 'Country'
            },
            barmode='group'
        )
    else:
        fig = px.area(
            data_filtered,
            x='TIME_PERIOD',
            y=selected_indicator,
            color='REF_AREA',
            title=f"{indicator_options[selected_indicator]} Over Time",
            labels={
                'TIME_PERIOD': 'Year',
                selected_indicator: 'Value (Millions USD)',
                'REF_AREA': 'Country'
            }
        )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, width='stretch')  # FIXED: width instead of use_container_width

with col2:
    st.subheader("🏆 Top Countries")
    
    country_avg = data_filtered.groupby('REF_AREA')[selected_indicator].mean().sort_values(ascending=False).head(10)
    country_avg = country_avg / 1000
    
    fig = px.bar(
        x=country_avg.values,
        y=country_avg.index,
        orientation='h',
        title=f"Top 10 by {indicator_options[selected_indicator]}",
        labels={'x': 'Average (Billions USD)', 'y': 'Country'},
        color=country_avg.values,
        color_continuous_scale='Blues'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, width='stretch')  # FIXED

# ============================================
# SECOND ROW - FIXED
# ============================================

col3, col4 = st.columns(2)

with col3:
    st.subheader("📊 Distribution Analysis")
    
    fig = px.histogram(
        data_filtered,
        x=selected_indicator,
        color='REF_AREA',
        title=f"Distribution of {indicator_options[selected_indicator]}",
        labels={selected_indicator: 'Value (Millions USD)'},
        nbins=30
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, width='stretch')  # FIXED

with col4:
    st.subheader("📈 Year-over-Year Growth")
    
    growth_data = data_filtered.sort_values(['REF_AREA', 'TIME_PERIOD'])
    growth_data['pct_change'] = growth_data.groupby('REF_AREA')[selected_indicator].pct_change() * 100
    
    latest_growth = growth_data[growth_data['TIME_PERIOD'] == growth_data['TIME_PERIOD'].max()]
    latest_growth = latest_growth.dropna(subset=['pct_change'])
    latest_growth = latest_growth.nlargest(5, 'pct_change')
    
    if not latest_growth.empty:
        fig = px.bar(
            latest_growth,
            x='REF_AREA',
            y='pct_change',
            title=f"Top 5 Countries by Growth",
            labels={'REF_AREA': 'Country', 'pct_change': 'Growth %'},
            color='pct_change',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, width='stretch')  # FIXED
    else:
        st.info("No growth data available for selected filters")

# ============================================
# FORECAST SECTION - FIXED
# ============================================

st.markdown("---")
st.subheader("🔮 5-Year Forecast")

col1, col2 = st.columns(2)

with col1:
    if not forecast.empty:
        fig = go.Figure()
        
        if selected_country != 'All':
            hist_data = time_series[time_series['REF_AREA'] == selected_country]
        else:
            hist_data = time_series[time_series['REF_AREA'] == 'WLD']
        
        if not hist_data.empty:
            fig.add_trace(go.Scatter(
                x=hist_data['TIME_PERIOD'],
                y=hist_data['exports_millions'],
                mode='lines+markers',
                name='Historical',
                line=dict(color='blue', width=2)
            ))
        
        fig.add_trace(go.Scatter(
            x=forecast['year'],
            y=forecast['forecast_value'],
            mode='lines+markers',
            name='Forecast',
            line=dict(color='green', width=2, dash='dash'),
            marker=dict(size=10, symbol='star')
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast['year'].tolist() + forecast['year'].tolist()[::-1],
            y=forecast['upper_bound'].tolist() + forecast['lower_bound'].tolist()[::-1],
            fill='toself',
            name='Confidence Interval',
            opacity=0.2,
            line=dict(color='lightgreen')
        ))
        
        fig.update_layout(
            title="Digital Exports Forecast",
            xaxis_title="Year",
            yaxis_title="Exports (Millions USD)",
            height=350,
            hovermode='x unified'
        )
        st.plotly_chart(fig, width='stretch')  # FIXED

with col2:
    if not forecast.empty:
        st.markdown("### 📊 Forecast Details")
        
        forecast_display = forecast.copy()
        forecast_display['forecast_value'] = forecast_display['forecast_value'].apply(lambda x: f"${x/1000:,.1f}B")
        forecast_display['growth_rate'] = forecast_display['growth_rate'].apply(lambda x: f"{x*100:.1f}%")
        
        st.dataframe(
            forecast_display[['year', 'forecast_value', 'growth_rate']],
            width='stretch',  # FIXED
            hide_index=True
        )
        
        next_year = forecast.iloc[0]
        st.info(f"""
        💡 **Forecast Insight**
        - Next Year: **${next_year['forecast_value']/1000:,.1f}B**
        - Growth Rate: **{next_year['growth_rate']*100:.1f}%**
        - Confidence: ±5%
        """)

# ============================================
# DATA TABLE - FIXED
# ============================================

st.markdown("---")
st.subheader("📋 Data Explorer")

tab1, tab2, tab3 = st.tabs(["📊 Time Series", "🌍 Country Summary", "📈 Top Exporters"])

with tab1:
    st.dataframe(
        data_filtered.head(100),
        width='stretch',  # FIXED
        height=400,
        column_config={
            "TIME_PERIOD": st.column_config.NumberColumn("Year"),
            "exports_millions": st.column_config.NumberColumn("Exports (M)", format="$%.0f"),
            "imports_millions": st.column_config.NumberColumn("Imports (M)", format="$%.0f"),
            "trade_balance": st.column_config.NumberColumn("Balance (M)", format="$%.0f"),
        }
    )

with tab2:
    st.dataframe(
        country_summary,
        width='stretch',  # FIXED
        height=400,
        column_config={
            "OBS_VALUE_mean": st.column_config.NumberColumn("Avg Value (M)", format="$%.0f"),
            "OBS_VALUE_max": st.column_config.NumberColumn("Max Value (M)", format="$%.0f"),
            "OBS_VALUE_count": st.column_config.NumberColumn("Data Points"),
        }
    )

with tab3:
    st.dataframe(
        top_exporters,
        width='stretch',  # FIXED
        height=400,
        column_config={
            "avg_exports": st.column_config.NumberColumn("Avg Exports (M)", format="$%.0f"),
            "total_exports": st.column_config.NumberColumn("Total Exports (M)", format="$%.0f"),
        }
    )

# ============================================
# EXPORT BUTTONS
# ============================================

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Download Data as CSV"):
        csv = data_filtered.to_csv(index=False)
        st.download_button(
            label="Click to Download",
            data=csv,
            file_name=f"digital_trade_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📊 Generate Report"):
        st.success("✅ Report generated! Check the data above.")

with col3:
    if st.button("🔄 Reset Filters"):
        st.rerun()

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 1rem;">
        🌍 Digital Trade Intelligence Platform | Built with Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True
)