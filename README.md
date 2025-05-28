
# Disclaimer
I'm actually vibe coding this entire thing, just to try and see how good the results will be.

# Stablecoin Reserve Shock

This repository contains code and data for analyzing stablecoin reserve shocks, including data ingestion, exploratory data analysis, VAR modeling, and event studies. It is organized for reproducible research and includes a pipeline from raw data to paper-ready figures and results.

## Repo Layout
```
root/
├── data/           # raw & processed datasets
│   ├── raw/
│   └── processed/
├── external/       # PDFs, issuer attestations
├── notebooks/      # analysis in chronological order
│   ├── 01_data_ingestion.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_var_model.ipynb
│   └── 04_event_study.ipynb
├── scripts/        # standalone Python helpers
│   ├── fetch_defillama_stablecoins.py
│   ├── fetch_fred_yields.py
│   ├── build_transactions_dataset.py
│   └── make_features.py
├── paper/          # research article
│   ├── draft.tex
│   ├── references.bib
│   └── figures/
├── dashboard/      # optional Plotly Dash app
│   └── app.py
├── requirements.txt
├── Makefile        # one-click data → paper pipeline
└── README.md
```

## Environment Quick-Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make all  # runs ingestion, EDA, VAR, exports figs & paper PDF
```

### Critical Libraries
- pandas
- numpy
- statsmodels
- web3.py
- fredapi
- typer
- nbqa
- black

## Publishing
This repo is set up for easy publishing to GitHub. After connecting your GitHub account and installing the GitHub CLI (`gh`), you can run:
```bash
git add .
git commit -m "Initial project structure"
gh repo create stablecoin_reserve_shock --public --source=. --remote=origin --push
```
