import requests
import pandas as pd
from typing import Dict, List
from .base_fetcher import BaseDataFetcher

class FMPFetcher(BaseDataFetcher):
    def __init__(self, config_path: str = "buffetology/config/config.yaml"):
        super().__init__(config_path)
        self.api_key = self.config['data_provider']['fmp']['api_key']
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    def _make_request(self, endpoint: str) -> Dict:
        url = f"{self.base_url}/{endpoint}?apikey={self.api_key}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_financial_statements(self, ticker: str) -> Dict[str, pd.DataFrame]:
        cache_path = self._get_cache_path(ticker, "financial_statements")
        cached_data = self._load_from_cache(cache_path)
        if cached_data is not None:
            return {
                "income": cached_data[cached_data['statement'] == 'income'],
                "balance": cached_data[cached_data['statement'] == 'balance'],
                "cashflow": cached_data[cached_data['statement'] == 'cashflow']
            }
        
        # Fetch financial statements
        income = pd.DataFrame(self._make_request(f"income-statement/{ticker}?limit=120"))
        balance = pd.DataFrame(self._make_request(f"balance-sheet-statement/{ticker}?limit=120"))
        cashflow = pd.DataFrame(self._make_request(f"cash-flow-statement/{ticker}?limit=120"))
        
        # Add statement type for caching
        income['statement'] = 'income'
        balance['statement'] = 'balance'
        cashflow['statement'] = 'cashflow'
        
        # Combine for caching
        combined = pd.concat([income, balance, cashflow])
        self._save_to_cache(combined, cache_path)
        
        return {
            "income": income,
            "balance": balance,
            "cashflow": cashflow
        }
    
    def get_key_metrics(self, ticker: str) -> pd.DataFrame:
        cache_path = self._get_cache_path(ticker, "key_metrics")
        cached_data = self._load_from_cache(cache_path)
        if cached_data is not None:
            return cached_data
        
        # Fetch key metrics
        metrics_data = self._make_request(f"key-metrics/{ticker}?limit=1")[0]
        
        metrics = pd.DataFrame({
            'metric': [
                'market_cap',
                'trailing_pe',
                'forward_pe',
                'peg_ratio',
                'price_to_book',
                'debt_to_equity',
                'current_ratio',
                'return_on_equity',
                'return_on_assets',
                'profit_margins',
                'revenue_growth',
                'earnings_growth'
            ],
            'value': [
                metrics_data.get('marketCap', None),
                metrics_data.get('peRatio', None),
                metrics_data.get('forwardPE', None),
                metrics_data.get('pegRatio', None),
                metrics_data.get('pbRatio', None),
                metrics_data.get('debtToEquity', None),
                metrics_data.get('currentRatio', None),
                metrics_data.get('roe', None),
                metrics_data.get('roa', None),
                metrics_data.get('netProfitMargin', None),
                metrics_data.get('revenueGrowth', None),
                metrics_data.get('earningsGrowth', None)
            ]
        })
        
        self._save_to_cache(metrics, cache_path)
        return metrics
    
    def get_stock_price(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        cache_path = self._get_cache_path(ticker, f"price_{start_date}_{end_date}")
        cached_data = self._load_from_cache(cache_path)
        if cached_data is not None:
            return cached_data
        
        # Fetch historical price data
        price_data = self._make_request(f"historical-price-full/{ticker}?from={start_date}&to={end_date}")
        hist = pd.DataFrame(price_data['historical'])
        hist['date'] = pd.to_datetime(hist['date'])
        hist.set_index('date', inplace=True)
        
        self._save_to_cache(hist, cache_path)
        return hist
    
    def get_sp500_tickers(self, limit: int) -> List[str]:
        cache_path = self._get_cache_path("sp500", "tickers")
        cached_data = self._load_from_cache(cache_path)
        if cached_data is not None:
            return cached_data['ticker'].head(limit).tolist()
        
        # Fetch S&P 500 components
        sp500_data = self._make_request("sp500_constituent")
        tickers = [item['symbol'] for item in sp500_data]
        
        # Cache the results
        ticker_df = pd.DataFrame({'ticker': tickers})
        self._save_to_cache(ticker_df, cache_path)
        
        return tickers[:limit] 