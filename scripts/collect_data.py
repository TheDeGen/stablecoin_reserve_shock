import pandas as pd

def collect_data():
    # Collect stablecoin data
    stablecoin_data = collect_stablecoin_data()
    
    # Collect Treasury yield data
    treasury_data = collect_treasury_data()
    
    # Merge datasets
    df = pd.merge(stablecoin_data, treasury_data, on='date', how='inner')
    
    # Filter for the study period
    df = df[(df['date'] >= '2024-11-01') & (df['date'] <= '2025-04-30')]
    
    # Save to CSV
    df.to_csv('data/stablecoin_treasury_data.csv', index=False)
    print("Data collection complete. Dataset saved to data/stablecoin_treasury_data.csv")
    
    return df 