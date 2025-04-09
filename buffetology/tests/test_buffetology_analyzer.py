import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime
from typing import Dict

from buffetology.analysis.buffetology_analyzer import BuffetologyAnalyzer
from buffetology.data_fetchers.yahoo_fetcher import YahooFinanceFetcher
from buffetology.config.config_loader import ConfigLoader

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return {
        'data_provider': {
            'default': 'yahoo',
            'yahoo': {
                'enabled': True
            }
        },
        'analysis': {
            'sp500_top_n': 50,
            'min_eps_growth': 0.15,
            'min_revenue_growth': 0.10,
            'years_of_history': 5,
            'debt_to_equity_threshold': 0.5,
            'min_current_ratio': 1.5,
            'min_roe': 0.15,
            'max_pe_ratio': 25,
            'max_pb_ratio': 3,
            'max_peg_ratio': 2,
            'min_market_cap': 1000000000,
            'min_profit_margin': 0.1,
            'min_earnings_growth': 0.15
        },
        'cache': {
            'enabled': True,
            'directory': 'tests/cache',
            'expiry_days': 7
        },
        'output': {
            'format': 'json',
            'directory': 'tests/output'
        }
    }

@pytest.fixture
def config(mock_config):
    """Load the mock configuration."""
    return ConfigLoader(mock_config)

@pytest.fixture
def mock_data_fetcher():
    """Create a mock data fetcher for testing."""
    fetcher = Mock(spec=YahooFinanceFetcher)
    
    # Mock financial statements
    dates = pd.date_range(end=datetime.now(), periods=4, freq='QE')
    financials = {
        'income': pd.DataFrame({
            'Revenue': [100, 120, 144, 173],
            'Net Income': [20, 25, 31, 38]
        }, index=dates),
        'balance': pd.DataFrame({
            'Total Assets': [200, 220, 240, 264],
            'Total Liabilities': [60, 65, 70, 77],
            'Total Debt': [40, 42, 45, 50],
            'Current Assets': [100, 110, 120, 132],
            'Current Liabilities': [40, 42, 45, 50]
        }, index=dates),
        'cash': pd.DataFrame({
            'Operating Cash Flow': [30, 35, 40, 46],
            'Free Cash Flow': [25, 29, 34, 39]
        }, index=dates)
    }
    
    # Mock key metrics
    metrics = pd.DataFrame([{
        'debtToEquity': 0.3,
        'currentRatio': 2.5,
        'returnOnEquity': 0.25,
        'profitMargins': 0.2,
        'priceToBook': 2.0,
        'trailingPE': 15.0,
        'pegRatio': 1.2,
        'marketCap': 1000000000,
        'revenueGrowth': 0.2,
        'earningsGrowth': 0.25
    }])
    
    # Mock stock price
    price_data = pd.DataFrame({
        'Close': [100, 105, 110, 115]
    }, index=dates)
    
    fetcher.get_financial_statements.return_value = financials
    fetcher.get_key_metrics.return_value = metrics
    fetcher.get_stock_price.return_value = price_data
    fetcher.get_sp500_tickers.return_value = ['AAPL', 'MSFT', 'GOOGL']
    
    return fetcher

@pytest.fixture
def analyzer(mock_data_fetcher, config):
    """Create an analyzer instance for testing."""
    return BuffetologyAnalyzer(mock_data_fetcher, config)

def test_analyze_ticker(analyzer):
    """Test analyzing a single ticker."""
    result = analyzer.analyze_ticker('AAPL')
    assert result['quality_score'] > 0
    assert result['value_score'] > 0
    assert result['growth_score'] > 0
    assert result['overall_score'] > 0
    assert 'recommendation' in result

def test_calculate_quality_score(analyzer):
    """Test quality score calculation."""
    metrics = analyzer.data_fetcher.get_key_metrics('AAPL')
    score = analyzer._calculate_quality_score(metrics)
    assert 0 <= score <= 100

def test_calculate_value_score(analyzer):
    """Test value score calculation."""
    metrics = analyzer.data_fetcher.get_key_metrics('AAPL')
    score = analyzer._calculate_value_score(metrics)
    assert 0 <= score <= 100

def test_calculate_growth_score(analyzer):
    """Test growth score calculation."""
    metrics = analyzer.data_fetcher.get_key_metrics('AAPL')
    score = analyzer._calculate_growth_score(metrics)
    assert 0 <= score <= 100

def test_invalid_ticker(analyzer):
    """Test handling of invalid ticker."""
    analyzer.data_fetcher.get_key_metrics.return_value = pd.DataFrame()
    result = analyzer.analyze_ticker('INVALID')
    assert result['overall_score'] == 0
    assert result['recommendation'] == 'Not enough data'

def test_insufficient_data(analyzer):
    """Test handling of insufficient data."""
    analyzer.data_fetcher.get_key_metrics.return_value = pd.DataFrame([{
        'debtToEquity': 0.3
    }])
    result = analyzer.analyze_ticker('AAPL')
    assert result['overall_score'] == 0
    assert result['recommendation'] == 'Not enough data'

def test_analyze_good_stock(analyzer):
    """Test analyzing a stock with good metrics."""
    # Mock excellent metrics
    metrics = pd.DataFrame([{
        'returnOnEquity': 0.25,
        'debtToEquity': 0.3,
        'currentRatio': 3.0,
        'profitMargins': 0.25,
        'priceToBook': 2.0,
        'trailingPE': 12.0,
        'pegRatio': 1.0,
        'marketCap': 5000000000,
        'revenueGrowth': 0.20,
        'earningsGrowth': 0.25
    }])
    analyzer.data_fetcher.get_key_metrics.return_value = metrics
    
    result = analyzer.analyze_ticker('GOOD')
    assert result['overall_score'] >= 80
    assert result['recommendation'] == 'Strong Buy'

def test_analyze_bad_stock(analyzer):
    """Test analyzing a stock with poor metrics."""
    # Mock poor metrics
    metrics = pd.DataFrame([{
        'returnOnEquity': 0.05,
        'debtToEquity': 1.5,
        'currentRatio': 0.8,
        'profitMargins': 0.02,
        'priceToBook': 5.0,
        'trailingPE': 50.0,
        'pegRatio': 3.0,
        'marketCap': 500000000,
        'revenueGrowth': -0.05,
        'earningsGrowth': -0.10
    }])
    analyzer.data_fetcher.get_key_metrics.return_value = metrics
    
    result = analyzer.analyze_ticker('BAD')
    assert result['overall_score'] < 30
    assert result['recommendation'] == 'Strong Sell'

def test_analyze_multiple_stocks(analyzer):
    """Test analyzing multiple stocks."""
    results = analyzer.analyze_stocks(['AAPL', 'MSFT', 'GOOGL'])
    assert isinstance(results, pd.DataFrame)
    assert len(results) == 3
    assert all(col in results.columns for col in ['ticker', 'overall_score', 'recommendation'])

def test_calculate_debt_ratio(analyzer):
    """Test debt ratio calculation."""
    metrics = pd.DataFrame([{
        'debtToEquity': 0.4
    }])
    
    score = analyzer._analyze_debt(metrics)
    assert 0 <= score <= 100

def test_config_validation(analyzer):
    """Test configuration validation."""
    assert analyzer.config is not None
    analysis_config = analyzer.config.get_analysis_config()
    assert 'min_eps_growth' in analysis_config
    assert 'min_revenue_growth' in analysis_config
    assert 'min_roe' in analysis_config

def test_recommendation_logic(analyzer):
    """Test the recommendation logic."""
    # Mock data for a good investment
    metrics = pd.DataFrame([{
        'returnOnEquity': 0.25,
        'debtToEquity': 0.3,
        'currentRatio': 2.5,
        'profitMargins': 0.15,
        'priceToBook': 2.0,
        'trailingPE': 15.0,
        'pegRatio': 1.2,
        'marketCap': 1000000000,
        'revenueGrowth': 0.20,
        'earningsGrowth': 0.25
    }])
    
    analyzer.data_fetcher.get_key_metrics.return_value = metrics
    result = analyzer.analyze_ticker('GOOD')
    assert result['overall_score'] > 70  # Good stock should have high score
    assert result['recommendation'] in ['Buy', 'Strong Buy']

def test_eps_growth_analysis(analyzer):
    """Test EPS growth score calculation."""
    metrics = pd.DataFrame([{
        'earningsGrowth': 0.20
    }])
    
    score = analyzer._analyze_eps_growth(metrics)
    assert 0 <= score <= 100

def test_debt_analysis(analyzer):
    """Test debt analysis score calculation."""
    metrics = pd.DataFrame([{
        'debtToEquity': 0.3  # Below threshold
    }])
    
    score = analyzer._analyze_debt(metrics)
    assert 0 <= score <= 100

def test_profitability_analysis(analyzer):
    """Test profitability score calculation."""
    metrics = pd.DataFrame([{
        'returnOnEquity': 0.20,
        'profitMargins': 0.15
    }])
    
    score = analyzer._analyze_profitability(metrics)
    assert 0 <= score <= 100

def test_error_handling(analyzer):
    """Test error handling in the analyzer."""
    analyzer.data_fetcher.get_key_metrics.side_effect = Exception("API Error")
    result = analyzer.analyze_ticker('ERROR')
    assert result['overall_score'] == 0
    assert result['recommendation'] == 'Error'

def test_analyze_sp500(analyzer):
    """Test analyzing S&P 500 stocks."""
    results = analyzer.analyze_sp500()
    assert isinstance(results, pd.DataFrame)
    assert len(results) > 0
    assert all(col in results.columns for col in ['ticker', 'overall_score', 'recommendation']) 