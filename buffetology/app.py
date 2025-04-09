import os
import yaml
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from tabulate import tabulate
import pandas as pd

from buffetology.config.config_loader import ConfigLoader
from buffetology.cache.cache_manager import CacheManager
from buffetology.data_fetchers.yahoo_fetcher import YahooFinanceFetcher
from buffetology.data_fetchers.fmp_fetcher import FMPFetcher
from buffetology.data_fetchers.ft_fetcher import FinancialTimesFetcher
from buffetology.analysis.buffetology_analyzer import BuffetologyAnalyzer

class BuffetologyApp:
    def __init__(self, config_path: str = "buffetology/config/config.yaml"):
        """Initialize the application with configuration."""
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.config
        self.cache_manager = CacheManager(
            self.config['cache']['directory'],
            self.config['cache']['expiry_days']
        )
        self.data_fetcher = self._initialize_data_fetcher()
        self.analyzer = BuffetologyAnalyzer(self.data_fetcher, self.config_loader)

    def _initialize_data_fetcher(self) -> YahooFinanceFetcher:
        """Initialize the appropriate data fetcher based on configuration."""
        provider = self.config['data_provider']['default']
        if provider == 'yahoo':
            return YahooFinanceFetcher(self.cache_manager, self.config)
        else:
            raise ValueError(f"Unsupported data provider: {provider}")

    def analyze_stocks(self, tickers: List[str], limit: Optional[int] = None) -> pd.DataFrame:
        """Analyze a list of stocks and return results as a DataFrame."""
        if limit:
            tickers = tickers[:limit]
        return self.analyzer.analyze_stocks(tickers)

    def analyze_sp500(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Analyze S&P 500 stocks and return results as a DataFrame."""
        sp500_tickers = self.data_fetcher.get_sp500_tickers()
        return self.analyze_stocks(sp500_tickers, limit)

    def run_analysis(self) -> None:
        """Run the Buffetology analysis on configured stocks."""
        try:
            # Get tickers to analyze
            tickers = self._get_analysis_tickers()
            
            print(f"Starting analysis of {len(tickers)} stocks...")
            
            # Run analysis
            results_df = self.analyzer.analyze_stocks(tickers)
            
            # Format and display results
            self._display_results(results_df)
            
        except Exception as e:
            print(f"Error running analysis: {str(e)}")

    def _get_analysis_tickers(self) -> List[str]:
        """Get the list of tickers to analyze based on configuration."""
        tickers = set()
        
        # Add custom tickers from config
        custom_tickers = self.config.get('analysis', {}).get('custom_tickers', [])
        tickers.update(custom_tickers)
        
        # Add top N SP500 tickers if configured
        sp500_top_n = self.config.get('analysis', {}).get('sp500_top_n', 0)
        if sp500_top_n > 0:
            sp500_tickers = self.data_fetcher.get_sp500_tickers()
            if sp500_tickers:  # Only add if we got some tickers
                tickers.update(sp500_tickers[:sp500_top_n])
            else:
                print("Warning: Failed to fetch S&P 500 tickers.")
        
        if not tickers:
            # Fallback to some default tickers if nothing else is available
            tickers.update(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'])
            print("Using default tickers as no other tickers were available.")
            
        return list(tickers)

    def _display_results(self, results_df) -> None:
        """Display analysis results in a formatted table."""
        if results_df.empty:
            print("No results to display.")
            return

        # Format the results table
        table = tabulate(
            results_df,
            headers='keys',
            tablefmt='pipe',
            floatfmt=".2f",
            showindex=False
        )
        
        print("\nBuffetology Analysis Results:")
        print("============================")
        print(table)

def get_data_fetcher() -> YahooFinanceFetcher:
    """Get a data fetcher instance for standalone use."""
    config_loader = ConfigLoader()
    config = config_loader.config
    cache_manager = CacheManager(
        config['cache']['directory'],
        config['cache']['expiry_days']
    )
    return YahooFinanceFetcher(cache_manager, config)

def format_results(df: pd.DataFrame, output_format: str) -> str:
    """Format the results according to the specified output format."""
    if output_format == 'table':
        return tabulate(df, headers='keys', tablefmt='grid', showindex=False)
    elif output_format == 'csv':
        return df.to_csv(index=False)
    elif output_format == 'json':
        return df.to_json(orient='records', indent=2)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

def main():
    """Main entry point for the application."""
    try:
        app = BuffetologyApp()
        
        # Get tickers from command line arguments
        if len(sys.argv) > 1:
            tickers = sys.argv[1:]
            print(f"Analyzing specified tickers: {', '.join(tickers)}")
            results_df = app.analyze_stocks(tickers)
            app._display_results(results_df)
        else:
            # If no tickers specified, analyze S&P 500
            print("No tickers specified. Analyzing S&P 500 stocks...")
            app.run_analysis()
            
    except Exception as e:
        print(f"Application error: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main()) 