import pytest
from unittest.mock import Mock, patch
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from buffetology.data_fetchers.yahoo_fetcher import YahooFinanceFetcher
from buffetology.cache.cache_manager import CacheManager

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        'data_provider': {
            'default': 'yahoo',
            'name': 'yahoo',
            'api_key': 'test_key'
        },
        'cache': {
            'enabled': True,
            'directory': 'test_cache',
            'expiry_days': 7
        },
        'analysis': {
            'min_eps_growth': 0.1,
            'min_revenue_growth': 0.1,
            'min_current_ratio': 1.5,
            'debt_to_equity_threshold': 0.5
        },
        'output': {
            'format': 'table',
            'path': 'results'
        }
    }

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache_manager = Mock()
    cache_manager.get.return_value = None
    return cache_manager

@pytest.fixture
def yahoo_fetcher(mock_config, mock_cache_manager):
    """Create a YahooFinanceFetcher instance with a mock cache manager."""
    return YahooFinanceFetcher(config=mock_config, cache_manager=mock_cache_manager)

def test_get_financial_statements(yahoo_fetcher):
    """Test fetching financial statements."""
    with patch('yfinance.Ticker') as mock_ticker:
        # Mock the yfinance Ticker object with proper date indices
        dates = pd.date_range(end=datetime.now(), periods=3, freq='YE')
        mock_stock = Mock()
        mock_stock.financials = pd.DataFrame({
            'Revenue': [100, 110, 121],
            'Net Income': [10, 12, 15]
        }, index=dates)
        mock_stock.balance_sheet = pd.DataFrame({
            'Total Assets': [200, 220, 240],
            'Total Liabilities': [80, 85, 90]
        }, index=dates)
        mock_stock.cashflow = pd.DataFrame({
            'Operating Cash Flow': [20, 22, 25],
            'Free Cash Flow': [15, 17, 20]
        }, index=dates)
        mock_ticker.return_value = mock_stock

        result = yahoo_fetcher.get_financial_statements('AAPL')
        assert isinstance(result, dict)
        assert all(isinstance(df, pd.DataFrame) for df in result.values())
        assert not any(df.empty for df in result.values())

def test_get_key_metrics(yahoo_fetcher):
    """Test fetching key metrics."""
    with patch('yfinance.Ticker') as mock_ticker:
        mock_stock = Mock()
        mock_stock.info = {
            'marketCap': 1000000000,
            'forwardPE': 15.5,
            'trailingPE': 16.2,
            'priceToBook': 5.4,
            'returnOnEquity': 0.25,
            'returnOnAssets': 0.15,
            'currentRatio': 2.1,
            'debtToEquity': 0.45,
            'profitMargins': 0.20,
            'revenueGrowth': 0.15,
            'earningsGrowth': 0.18,
            'pegRatio': 1.2
        }
        mock_ticker.return_value = mock_stock

        result = yahoo_fetcher.get_key_metrics('AAPL')
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result) == 1
        assert all(key in result.columns for key in mock_stock.info.keys())

def test_get_sp500_tickers(yahoo_fetcher):
    """Test fetching S&P 500 tickers."""
    with patch('yfinance.Ticker') as mock_ticker:
        mock_stock = Mock()
        mock_stock.info = {
            'components': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
        }
        mock_ticker.return_value = mock_stock

        result = yahoo_fetcher.get_sp500_tickers(limit=3)
        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(ticker, str) for ticker in result)

def test_get_stock_price(yahoo_fetcher):
    """Test fetching stock prices."""
    with patch('yfinance.Ticker') as mock_ticker:
        dates = pd.date_range(start='2023-01-01', end='2023-01-03', freq='D')
        mock_stock = Mock()
        mock_stock.history.return_value = pd.DataFrame({
            'Close': [100, 102, 105],
            'Open': [99, 101, 104],
            'High': [101, 103, 106],
            'Low': [98, 100, 103]
        }, index=dates)
        mock_ticker.return_value = mock_stock

        result = yahoo_fetcher.get_stock_price('AAPL', '2023-01-01', '2023-01-03')
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert all(col in result.columns for col in ['Close', 'Open', 'High', 'Low'])

def test_cache_hit(yahoo_fetcher, mock_cache_manager):
    """Test cache hit functionality."""
    cached_data = {
        'income': {'Revenue': [100, 110], 'Net Income': [10, 12]},
        'balance': {'Total Assets': [200, 220], 'Total Liabilities': [80, 85]},
        'cash': {'Operating Cash Flow': [20, 22], 'Free Cash Flow': [15, 17]}
    }
    mock_cache_manager.get.return_value = cached_data

    result = yahoo_fetcher.get_financial_statements('AAPL')
    assert isinstance(result, dict)
    assert all(isinstance(df, pd.DataFrame) for df in result.values())
    assert not any(df.empty for df in result.values())

def test_cache_functionality(yahoo_fetcher, mock_cache_manager):
    """Test that cache is being used."""
    with patch('yfinance.Ticker') as mock_ticker:
        dates = pd.date_range(end=datetime.now(), periods=3, freq='YE')
        mock_stock = Mock()
        mock_stock.financials = pd.DataFrame({
            'Revenue': [100, 110, 121],
            'Net Income': [10, 12, 15]
        }, index=dates)
        mock_stock.balance_sheet = pd.DataFrame({
            'Total Assets': [200, 220, 240],
            'Total Liabilities': [80, 85, 90]
        }, index=dates)
        mock_stock.cashflow = pd.DataFrame({
            'Operating Cash Flow': [20, 22, 25],
            'Free Cash Flow': [15, 17, 20]
        }, index=dates)
        mock_ticker.return_value = mock_stock

        yahoo_fetcher.get_financial_statements('AAPL')
        assert mock_cache_manager.set.call_count > 0

def test_error_handling(yahoo_fetcher):
    """Test error handling."""
    with patch('yfinance.Ticker') as mock_ticker:
        mock_ticker.side_effect = Exception("API Error")
        with pytest.raises(ValueError):
            yahoo_fetcher.get_financial_statements('INVALID') 