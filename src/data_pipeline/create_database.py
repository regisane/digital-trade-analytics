
"""
SQL DATABASE CREATION - FULLY FIXED
Senior Data Engineer - Production Ready
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

print("=" * 70)
print("🗄️  CREATING SQL DATABASE (FIXED)")
print("=" * 70)

DB_PATH = 'data/digital_trade.db'

# Remove existing database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("✅ Removed existing database")

# Load data
print("\n📥 Loading data...")

df_raw = pd.read_csv('data/raw/unctad_digital_trade.csv')
print(f"✅ Raw data: {len(df_raw):,} rows")

# Load or create processed data
processed_path = 'data/processed/trade_data_processed.csv'
if os.path.exists(processed_path):
    df_processed = pd.read_csv(processed_path)
    print(f"✅ Processed data: {len(df_processed):,} rows")
else:
    print("⚠️  Processing raw data...")
    df_processed = df_raw[
        (df_raw['REF_AREA'] == 'WLD') & 
        (df_raw['INDICATOR'] == 'UNCTAD_DE_DIG_SERVTRADE_ANN_EXP')
    ].copy()
    df_processed = df_processed.sort_values('TIME_PERIOD')
    df_processed['prev_value'] = df_processed['OBS_VALUE'].shift(1)
    df_processed = df_processed.dropna(subset=['prev_value'])
    df_processed.to_csv(processed_path, index=False)

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
print("\n🏗️  Creating tables...")

# 1. Raw Data
df_raw.to_sql('raw_trade_data', conn, if_exists='replace', index=False)
print("✅ raw_trade_data")

# 2. Processed Data
df_processed.to_sql('processed_trade_data', conn, if_exists='replace', index=False)
print("✅ processed_trade_data")

# 3. Time Series Data
print("\n⏰ Creating time_series_data...")

time_series = df_raw.pivot_table(
    index=['REF_AREA', 'TIME_PERIOD'],
    columns='INDICATOR',
    values='OBS_VALUE',
    aggfunc='first'
).reset_index()

time_series.columns.name = None
time_series.rename(columns={
    'UNCTAD_DE_DIG_SERVTRADE_ANN_EXP': 'exports_millions',
    'UNCTAD_DE_DIG_SERVTRADE_ANN_IMP': 'imports_millions'
}, inplace=True)

time_series['trade_balance'] = time_series['exports_millions'] - time_series['imports_millions']
time_series.to_sql('time_series_data', conn, if_exists='replace', index=False)
print("✅ time_series_data")

# 4. Country Summary
print("\n📊 Creating country_summary...")

country_names = {
    'WLD': 'World', 'SSF': 'Sub-Saharan Africa',
    'USA': 'United States', 'CHN': 'China', 'IND': 'India',
    'GBR': 'United Kingdom', 'DEU': 'Germany', 'FRA': 'France',
    'JPN': 'Japan', 'AUS': 'Australia', 'CAN': 'Canada',
    'BRA': 'Brazil', 'MEX': 'Mexico', 'KOR': 'Korea, Rep.',
    'SGP': 'Singapore', 'ZAF': 'South Africa', 'RUS': 'Russian Federation',
    'ITA': 'Italy', 'ESP': 'Spain', 'ARG': 'Argentina',
    'TUR': 'Turkiye', 'NLD': 'Netherlands', 'CHE': 'Switzerland',
    'IRL': 'Ireland', 'SWE': 'Sweden', 'NOR': 'Norway',
    'POL': 'Poland', 'UKR': 'Ukraine', 'ISR': 'Israel',
}

country_summary = df_raw.groupby('REF_AREA').agg({
    'OBS_VALUE': ['mean', 'max', 'min', 'count'],
    'TIME_PERIOD': ['min', 'max']
}).round(2)

country_summary.columns = ['_'.join(col).strip() for col in country_summary.columns.values]
country_summary = country_summary.reset_index()
country_summary['country_name'] = country_summary['REF_AREA'].map(country_names)
country_summary['country_name'] = country_summary['country_name'].fillna(country_summary['REF_AREA'])

country_summary.to_sql('country_summary', conn, if_exists='replace', index=False)
print("✅ country_summary")

# ============================================
# CREATE VIEWS - ALL FIXED!
# ============================================

print("\n👁️  Creating views...")

# VIEW 1: Top Exporters - FIXED: Use aliases!
cursor.execute("""
CREATE VIEW IF NOT EXISTS top_exporters AS
SELECT 
    ts.REF_AREA AS country_code,
    cs.country_name,
    AVG(ts.exports_millions) AS avg_exports,
    SUM(ts.exports_millions) AS total_exports,
    COUNT(*) AS years_data
FROM time_series_data ts
LEFT JOIN country_summary cs ON ts.REF_AREA = cs.REF_AREA
WHERE ts.exports_millions IS NOT NULL
GROUP BY ts.REF_AREA
ORDER BY avg_exports DESC
LIMIT 10
""")
print("✅ top_exporters")

# VIEW 2: Year-over-Year Growth - FIXED
cursor.execute("""
CREATE VIEW IF NOT EXISTS yoy_growth AS
SELECT 
    REF_AREA AS country_code,
    TIME_PERIOD AS year,
    exports_millions,
    LAG(exports_millions, 1) OVER (PARTITION BY REF_AREA ORDER BY TIME_PERIOD) AS prev_year,
    ROUND(
        ((exports_millions - LAG(exports_millions, 1) OVER (PARTITION BY REF_AREA ORDER BY TIME_PERIOD)) / 
         NULLIF(LAG(exports_millions, 1) OVER (PARTITION BY REF_AREA ORDER BY TIME_PERIOD), 0)) * 100, 
        2
    ) AS growth_pct
FROM time_series_data
WHERE exports_millions IS NOT NULL
""")
print("✅ yoy_growth")

# VIEW 3: Global Summary - FIXED
cursor.execute("""
CREATE VIEW IF NOT EXISTS global_summary AS
SELECT 
    (SELECT MAX(TIME_PERIOD) FROM time_series_data) AS latest_year,
    (SELECT SUM(exports_millions) FROM time_series_data WHERE REF_AREA = 'WLD') AS total_exports,
    (SELECT SUM(imports_millions) FROM time_series_data WHERE REF_AREA = 'WLD') AS total_imports,
    (SELECT COUNT(DISTINCT REF_AREA) FROM time_series_data) AS total_countries,
    (SELECT AVG(exports_millions) FROM time_series_data WHERE REF_AREA != 'WLD') AS avg_country_exports
""")
print("✅ global_summary")

# VIEW 4: Top Exporters by Year - FIXED!
cursor.execute("""
CREATE VIEW IF NOT EXISTS top_exporters_by_year AS
SELECT 
    TIME_PERIOD AS year,
    REF_AREA AS country_code,
    exports_millions,
    RANK() OVER (PARTITION BY TIME_PERIOD ORDER BY exports_millions DESC) AS rank
FROM time_series_data
WHERE exports_millions IS NOT NULL
""")
print("✅ top_exporters_by_year")

# ============================================
# TEST THE DATABASE
# ============================================

print("\n🧪 Testing database queries...")

# Test 1: Top Exporters
print("\n📊 Top Exporters:")
top_exporters = pd.read_sql("SELECT country_code, country_name, avg_exports FROM top_exporters LIMIT 5", conn)
print(top_exporters.to_string(index=False))

# Test 2: Global Summary
global_summary = pd.read_sql("SELECT * FROM global_summary", conn)
print(f"\n🌍 Global Summary:")
print(f"  Latest Year: {int(global_summary['latest_year'].iloc[0])}")
print(f"  Total Exports: ${global_summary['total_exports'].iloc[0]:,.0f}M")
print(f"  Total Countries: {int(global_summary['total_countries'].iloc[0])}")

# Test 3: Top Exporters by Year (NEW!)
print("\n📈 Top Exporters by Year (2023):")
top_by_year = pd.read_sql("""
SELECT country_code, year, exports_millions, rank 
FROM top_exporters_by_year 
WHERE year = 2023 
ORDER BY rank 
LIMIT 5
""", conn)
print(top_by_year.to_string(index=False))

# ============================================
# CREATE FORECAST TABLE
# ============================================

print("\n🔮 Creating forecast table...")

last_year = int(df_processed['TIME_PERIOD'].max())
last_value = df_processed['OBS_VALUE'].iloc[-1]

forecast_data = []
current_year = last_year
current_value = last_value

for i in range(1, 6):
    growth_rate = 0.05 - (i * 0.005)
    next_value = current_value * (1 + growth_rate)
    
    forecast_data.append({
        'year': current_year + i,
        'forecast_value': round(next_value, 2),
        'lower_bound': round(next_value * 0.95, 2),
        'upper_bound': round(next_value * 1.05, 2),
        'growth_rate': growth_rate,
        'scenario': 'base'
    })
    
    current_year += 1
    current_value = next_value

df_forecast = pd.DataFrame(forecast_data)
df_forecast.to_sql('forecast_results', conn, if_exists='replace', index=False)
print("✅ forecast_results")

# ============================================
# SUMMARY
# ============================================

print("\n📋 Database Summary:")
print("-" * 40)

tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print("Tables:")
for table in tables['name']:
    count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
    print(f"  • {table}: {count.iloc[0,0]:,} rows")

views = pd.read_sql("SELECT name FROM sqlite_master WHERE type='view'", conn)
print("\nViews:")
for view in views['name']:
    print(f"  • {view}")

conn.close()

print("\n" + "=" * 70)
print("✅ DATABASE CREATED SUCCESSFULLY!")
print("=" * 70)
print(f"📁 Database: {DB_PATH}")
print("\n💡 Next Steps:")
print("  1. Run: streamlit run src/dashboard/enhanced_dashboard.py")
print("  2. Connect Power BI to this database")
print("=" * 70)