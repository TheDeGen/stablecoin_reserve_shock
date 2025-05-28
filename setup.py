from setuptools import setup, find_packages

setup(
    name="stablecoin_reserve_shock",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "requests",
        "python-dotenv",
        "httpx",
        "tenacity",
    ],
    python_requires=">=3.8",
) 