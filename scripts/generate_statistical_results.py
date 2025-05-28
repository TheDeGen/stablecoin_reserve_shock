import pandas as pd
import numpy as np
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import grangercausalitytests
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style for plots
plt.style.use('seaborn-v0_8')
sns.set_theme(style="whitegrid")

def load_data():
    """Load and prepare the data for analysis."""
    # Load the data
    market_cap = pd.read_parquet('data/raw/stablecoin_caps.parq')
    treasury_yields = pd.read_parquet('data/raw/treasury_yields.parq')
    
    # Convert timestamp to datetime and set as index
    market_cap['timestamp'] = pd.to_datetime(market_cap['timestamp'])
    market_cap = market_cap.set_index('timestamp')
    # Rename for clarity
    market_cap = market_cap.rename(columns={'circulating_supply_usd': 'market_cap'})
    # Keep only the market cap column
    market_cap = market_cap[['market_cap']]
    
    # Align index to date only (remove time)
    market_cap.index = market_cap.index.date
    treasury_yields.index = pd.to_datetime(treasury_yields.index).date
    
    # Merge the data
    df = pd.merge(market_cap, treasury_yields, left_index=True, right_index=True)
    # Drop rows with missing values
    df = df.dropna()
    return df

def run_var_analysis(df, maxlags=5):
    """Run VAR analysis and return results."""
    # Prepare data for VAR
    var_data = df[['market_cap', 'DGS3MO', 'DGS1', 'DGS2', 'DGS5', 'DGS10', 'DGS30']]
    
    # Fit VAR model
    model = VAR(var_data)
    results = model.fit(maxlags=maxlags)
    
    return results

def run_granger_tests(df, maxlag=5):
    """Run Granger causality tests and return results."""
    granger_results = {}
    
    # Test each yield against market cap
    for col in ['DGS3MO', 'DGS1', 'DGS2', 'DGS5', 'DGS10', 'DGS30']:
        # Test if yield Granger-causes market cap
        gc_res1 = grangercausalitytests(df[['market_cap', col]], maxlag=maxlag, verbose=False)
        # Test if market cap Granger-causes yield
        gc_res2 = grangercausalitytests(df[[col, 'market_cap']], maxlag=maxlag, verbose=False)
        
        granger_results[col] = {
            'yield_to_marketcap': gc_res1,
            'marketcap_to_yield': gc_res2
        }
    
    return granger_results

def generate_additional_figures(df):
    """Generate additional figures for the paper."""
    # Create figures directory if it doesn't exist
    Path('figures').mkdir(exist_ok=True)
    
    # 1. Heatmap of correlations
    plt.figure(figsize=(12, 8))
    corr_matrix = df.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
    plt.title('Correlation Matrix: Market Cap and Treasury Yields')
    plt.tight_layout()
    plt.savefig('figures/correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Rolling volatility
    plt.figure(figsize=(12, 6))
    volatility = df['market_cap'].pct_change().rolling(window=20).std()
    plt.plot(volatility.index, volatility.values)
    plt.title('20-Day Rolling Volatility of Stablecoin Market Cap')
    plt.ylabel('Volatility')
    plt.grid(True)
    plt.savefig('figures/market_cap_volatility.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Yield curve changes
    plt.figure(figsize=(12, 6))
    yield_curves = df[['DGS3MO', 'DGS1', 'DGS2', 'DGS5', 'DGS10', 'DGS30']]
    yield_changes = yield_curves.pct_change().rolling(window=20).mean()
    plt.plot(yield_changes.index, yield_changes.values)
    plt.title('20-Day Rolling Average Yield Changes')
    plt.ylabel('Percentage Change')
    plt.legend(yield_changes.columns)
    plt.grid(True)
    plt.savefig('figures/yield_changes.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Market cap vs yield scatter with regression
    plt.figure(figsize=(10, 6))
    for col in ['DGS3MO', 'DGS1', 'DGS2', 'DGS5', 'DGS10', 'DGS30']:
        sns.regplot(data=df, x=col, y='market_cap', scatter_kws={'alpha':0.3}, label=col)
    plt.title('Market Cap vs Treasury Yields with Regression Lines')
    plt.xlabel('Yield (%)')
    plt.ylabel('Market Cap (Billions USD)')
    plt.legend()
    plt.savefig('figures/market_cap_vs_all_yields.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Load data
    df = load_data()
    
    # Run VAR analysis
    var_results = run_var_analysis(df)
    
    # Run Granger causality tests
    granger_results = run_granger_tests(df)
    
    # Generate additional figures
    generate_additional_figures(df)
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(df.describe())
    
    print("\nVAR Model Summary:")
    print(var_results.summary())
    
    print("\nGranger Causality Test Results:")
    for yield_type, results in granger_results.items():
        print(f"\n{yield_type}:")
        print("Yield to Market Cap:")
        print(f"F-statistic: {results['yield_to_marketcap'][1][0]['ssr_ftest'][0]:.2f}")
        print(f"p-value: {results['yield_to_marketcap'][1][0]['ssr_ftest'][1]:.4f}")
        print("Market Cap to Yield:")
        print(f"F-statistic: {results['marketcap_to_yield'][1][0]['ssr_ftest'][0]:.2f}")
        print(f"p-value: {results['marketcap_to_yield'][1][0]['ssr_ftest'][1]:.4f}")

if __name__ == "__main__":
    main() 