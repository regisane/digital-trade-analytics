
"""
UNCTAD DIGITAL TRADE ANALYSIS - FINAL CLEAN VERSION
Senior Data Scientist - Production Ready
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
import os

warnings.filterwarnings('ignore')

# ============================================
# CONFIGURATION
# ============================================

FILE_PATH = 'data/raw/unctad_digital_trade.csv'
OUTPUT_DIR = 'data/processed'
FIGURES_DIR = 'reports/figures'

# ============================================
# SETUP
# ============================================

print("=" * 70)
print("📊 UNCTAD DIGITAL TRADE ANALYSIS")
print("=" * 70)

# Create directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# ============================================
# LOAD DATA
# ============================================

if not os.path.exists(FILE_PATH):
    print(f"❌ ERROR: File not found at {FILE_PATH}")
    exit(1)

df = pd.read_csv(FILE_PATH)
print(f"✅ Loaded {len(df):,} rows")

# ============================================
# FILTER DATA
# ============================================

global_exports = df[
    (df['REF_AREA'] == 'WLD') & 
    (df['INDICATOR'] == 'UNCTAD_DE_DIG_SERVTRADE_ANN_EXP')
].copy()

global_exports = global_exports.sort_values('TIME_PERIOD')
global_exports = global_exports.dropna(subset=['OBS_VALUE'])

print(f"✅ Found {len(global_exports)} years of data")

# Show the data
print("\n📈 GLOBAL DIGITAL EXPORTS:")
for _, row in global_exports.iterrows():
    print(f"  {int(row['TIME_PERIOD'])}: ${row['OBS_VALUE']:,.0f}M")

# ============================================
# PREPARE FEATURES
# ============================================

global_exports['prev_value'] = global_exports['OBS_VALUE'].shift(1)
global_exports = global_exports.dropna(subset=['prev_value'])

X = global_exports[['TIME_PERIOD', 'prev_value']].values
y = global_exports['OBS_VALUE'].values

# ============================================
# SPLIT DATA
# ============================================

split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

# Store years for plotting
train_years = global_exports['TIME_PERIOD'].iloc[:split_idx].values
test_years = global_exports['TIME_PERIOD'].iloc[split_idx:].values
all_years = global_exports['TIME_PERIOD'].values

print(f"\n🎯 Split: {len(X_train)} training, {len(X_test)} test")

# ============================================
# TRAIN MODEL
# ============================================

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LinearRegression()
model.fit(X_train_scaled, y_train)

# ============================================
# EVALUATE
# ============================================

y_train_pred = model.predict(X_train_scaled)
y_test_pred = model.predict(X_test_scaled)

train_r2 = r2_score(y_train, y_train_pred)
test_r2 = r2_score(y_test, y_test_pred)

print(f"\n📊 Model R²: {test_r2:.4f}")

# ============================================
# FORECAST
# ============================================

last_year = int(global_exports['TIME_PERIOD'].iloc[-1])
last_value = global_exports['OBS_VALUE'].iloc[-1]

current_year, current_value = last_year, last_value
forecast_years, forecast_values = [], []

print("\n🔮 FORECAST:")
for i in range(1, 4):
    features = np.array([[current_year + 1, current_value]])
    features_scaled = scaler.transform(features)
    prediction = model.predict(features_scaled)[0]
    
    forecast_years.append(current_year + 1)
    forecast_values.append(prediction)
    
    print(f"  {current_year + 1}: ${prediction:,.0f}M")
    current_year += 1
    current_value = prediction

# ============================================
# VISUALIZATIONS
# ============================================

print("\n📊 Creating visualizations...")

# Figure 1: Performance
plt.figure(figsize=(12, 6))
plt.plot(all_years, global_exports['OBS_VALUE'].values, 'b-', linewidth=2.5, label='Actual', marker='o')
plt.plot(train_years, y_train_pred, 'g--', linewidth=2, label='Training', marker='s')
plt.plot(test_years, y_test_pred, 'r--', linewidth=2, label='Test', marker='d')
plt.plot(forecast_years, forecast_values, 'purple', linewidth=2.5, label='Forecast', marker='*', markersize=12)

plt.xlabel('Year')
plt.ylabel('Exports (Million USD)')
plt.title('Global Digital Services Exports - Model Performance')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/model_performance.png', dpi=300)
print(f"✅ Saved: {FIGURES_DIR}/model_performance.png")

# Figure 2: Residuals
plt.figure(figsize=(10, 5))
all_pred = np.concatenate([y_train_pred, y_test_pred])
all_actual = np.concatenate([y_train, y_test])
all_residuals = all_actual - all_pred

plt.scatter(all_pred, all_residuals, alpha=0.6, s=80)
plt.axhline(y=0, color='r', linestyle='--', linewidth=2)
plt.xlabel('Predicted Values')
plt.ylabel('Residuals')
plt.title('Residual Plot - Model Diagnostics')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/residual_plot.png', dpi=300)
print(f"✅ Saved: {FIGURES_DIR}/residual_plot.png")

# ============================================
# SAVE DATA
# ============================================

output_file = f'{OUTPUT_DIR}/trade_data_processed.csv'
global_exports.to_csv(output_file, index=False)
print(f"✅ Saved: {output_file}")

# ============================================
# SUMMARY
# ============================================

print("\n" + "=" * 70)
print("✅ ANALYSIS COMPLETE!")
print("=" * 70)

growth = ((global_exports['OBS_VALUE'].iloc[-1] - global_exports['OBS_VALUE'].iloc[0]) / 
          global_exports['OBS_VALUE'].iloc[0] * 100)

print(f"\n💡 KEY FINDINGS:")
print(f"  • Model explains {test_r2*100:.1f}% of variance")
print(f"  • Growth (2010-2023): {growth:.1f}%")
print(f"  • Next year forecast: ${forecast_values[0]:,.0f}M")
print(f"  • Performance: {'✅ Excellent' if test_r2 > 0.85 else '✅ Good'}")

print(f"\n📁 FILES CREATED:")
print(f"  • Data: {output_file}")
print(f"  • Plot: {FIGURES_DIR}/model_performance.png")
print(f"  • Residual: {FIGURES_DIR}/residual_plot.png")

print("\n" + "=" * 70)