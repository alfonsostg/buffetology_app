from setuptools import setup, find_packages

setup(
    name="buffetology",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "yfinance>=0.2.0",
        "pyyaml>=6.0",
        "tabulate>=0.9.0",
        "pytest>=7.0.0",
        "python-dateutil>=2.8.2",
        "requests>=2.28.0",
        "python-dotenv>=0.21.0",
        "beautifulsoup4>=4.11.0",
        "aiohttp>=3.8.0"
    ],
) 