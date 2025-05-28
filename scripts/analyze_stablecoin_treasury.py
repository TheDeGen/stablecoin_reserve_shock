#!/usr/bin/env python3
"""
Enhanced analysis of the relationship between stablecoin market cap and Treasury yields.
Includes more maturities, spreads, lagged and rolling correlations, and additional plots.
Saves plots to figures/ and outputs a text report with key findings.
"""
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Directories and files
RAW_DIR = Path("data/raw")
FIG_DIR = Path("figures")
REPORT_FILE = Path("figures/analysis_report.txt")
STABLECOIN_FILE = RAW_DIR / "stablecoin_caps.parq"
TREASURY_FILE = RAW_DIR / "treasury_yields.parq"

# Ensure figures directory exists
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Load data
stablecoins = pd.read_parquet(STABLECOIN_FILE)
treasury = pd.read_parquet(TREASURY_FILE)

# Preprocess stablecoin data
df_stable = stablecoins.copy()
df_stable = df_stable.rename(columns={"timestamp": "date"})
df_stable["date"] = pd.to_datetime(df_stable["date"])
df_stable = df_stable.set_index("date").sort_index()

# Preprocess treasury data
df_treasury = treasury.copy()

# Merge on date (inner join to keep only overlapping dates)
df = df_stable.join(df_treasury, how="inner")

# Drop rows with missing values in key columns
df = df.dropna(subset=["circulating_supply_usd", "DGS10", "DGS3MO"])

# --- Analysis ---
report_lines = []

# Summary statistics for all yields and spreads
cols_to_describe = [
    "circulating_supply_usd", "DGS3MO", "DGS1", "DGS2", "DGS5", "DGS10", "DGS30",
    "10Y-2Y", "10Y-3M", "2Y-3M"
]
existing_cols = [col for col in cols_to_describe if col in df.columns]
report_lines.append("Summary Statistics (all yields and spreads):\n")
report_lines.append(str(df[existing_cols].describe()))
report_lines.append("\n")

# Correlation matrix (all yields and spreads)
corr = df[existing_cols].corr()
report_lines.append("Correlation Matrix (all yields and spreads):\n")
report_lines.append(str(corr))
report_lines.append("\n")

# --- Lagged correlations ---
report_lines.append("Lagged Correlations (Stablecoin Market Cap vs. Yields/Spreads):\n")
for col in existing_cols[1:]:
    lag_corr = df["circulating_supply_usd"].corr(df[col].shift(5))  # 5-day lag
    report_lines.append(f"  5-day lag: circulating_supply_usd vs. {col}: {lag_corr:.3f}")
    lag_corr_20 = df["circulating_supply_usd"].corr(df[col].shift(20))  # 20-day lag
    report_lines.append(f"  20-day lag: circulating_supply_usd vs. {col}: {lag_corr_20:.3f}")
report_lines.append("\n")

# --- Rolling correlations ---
window = 30
report_lines.append(f"Rolling {window}-day Correlations (Stablecoin Market Cap vs. Yields/Spreads):\n")
for col in existing_cols[1:]:
    rolling_corr = df["circulating_supply_usd"].rolling(window).corr(df[col])
    plt.figure(figsize=(10, 4))
    rolling_corr.plot()
    plt.title(f"Rolling {window}-day Correlation: Market Cap vs. {col}")
    plt.ylabel("Correlation")
    plt.tight_layout()
    plt.savefig(FIG_DIR / f"rolling_corr_marketcap_{col}.png")
    plt.close()
    report_lines.append(f"  Saved rolling correlation plot for {col}.")
report_lines.append("\n")

# --- Visualization ---
# 1. Stablecoin market cap over time
plt.figure(figsize=(10, 6))
df["circulating_supply_usd"].plot(label="Stablecoin Market Cap (USD)", color="blue")
plt.ylabel("Stablecoin Market Cap (USD)")
plt.title("Stablecoin Market Cap Over Time")
plt.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "stablecoin_market_cap.png")
plt.close()

# 2. All Treasury yields over time
plt.figure(figsize=(10, 6))
df[[col for col in ["DGS3MO", "DGS1", "DGS2", "DGS5", "DGS10", "DGS30"] if col in df.columns]].plot()
plt.ylabel("Yield (%)")
plt.title("Treasury Yields (All Maturities)")
plt.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "treasury_yields_all.png")
plt.close()

# 3. All spreads over time
spread_cols = [col for col in ["10Y-2Y", "10Y-3M", "2Y-3M"] if col in df.columns]
if spread_cols:
    plt.figure(figsize=(10, 6))
    df[spread_cols].plot()
    plt.ylabel("Yield Spread (%)")
    plt.title("Treasury Yield Spreads")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "treasury_yield_spreads.png")
    plt.close()

# 4. Market cap vs. each yield (scatter)
for col in ["DGS3MO", "DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]:
    if col in df.columns:
        plt.figure(figsize=(7, 5))
        plt.scatter(df[col], df["circulating_supply_usd"], alpha=0.5)
        plt.xlabel(f"{col} Yield (%)")
        plt.ylabel("Stablecoin Market Cap (USD)")
        plt.title(f"Market Cap vs. {col} Yield")
        plt.tight_layout()
        plt.savefig(FIG_DIR / f"marketcap_vs_{col}.png")
        plt.close()

# 5. Market cap vs. each spread (scatter)
for col in spread_cols:
    plt.figure(figsize=(7, 5))
    plt.scatter(df[col], df["circulating_supply_usd"], alpha=0.5)
    plt.xlabel(f"{col} Spread (%)")
    plt.ylabel("Stablecoin Market Cap (USD)")
    plt.title(f"Market Cap vs. {col} Spread")
    plt.tight_layout()
    plt.savefig(FIG_DIR / f"marketcap_vs_{col}.png")
    plt.close()

# --- Key findings (simple) ---
if "DGS10" in df.columns:
    if corr.loc["circulating_supply_usd", "DGS10"] < -0.2:
        report_lines.append("There is a negative correlation between stablecoin market cap and 10Y Treasury yield.\n")
    elif corr.loc["circulating_supply_usd", "DGS10"] > 0.2:
        report_lines.append("There is a positive correlation between stablecoin market cap and 10Y Treasury yield.\n")
    else:
        report_lines.append("There is little to no correlation between stablecoin market cap and 10Y Treasury yield.\n")

# Save report
with open(REPORT_FILE, "w") as f:
    f.write("\n".join(report_lines))

print(f"Enhanced analysis complete. Plots saved to {FIG_DIR}/ and report saved to {REPORT_FILE}.") 