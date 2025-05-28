.PHONY: install test lint clean ingest paper

# Development
install:
	pip install -r requirements.txt
	pre-commit install

test:
	pytest tests/ --cov=scripts --cov-report=term-missing

lint:
	black scripts/ tests/
	isort scripts/ tests/
	flake8 scripts/ tests/
	mypy scripts/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

# Data pipeline
ingest:
	python scripts/ingest/fetch_stablecoin_caps.py
	python scripts/ingest/fetch_treasury_yields.py

# Paper
paper:
	cd paper && pdflatex main.tex
	bibtex main
	pdflatex main.tex
	pdflatex main.tex
