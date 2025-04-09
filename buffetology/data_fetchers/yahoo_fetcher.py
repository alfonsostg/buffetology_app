import pandas as pd
from typing import List, Optional, Dict, Any
import yfinance as yf
from buffetology.data_fetchers.base_fetcher import BaseDataFetcher

class YahooFinanceFetcher(BaseDataFetcher):
    def get_financial_statements(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """Get financial statements for a ticker."""
        cache_key = f"{ticker}_financials"
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return {
                'income': pd.DataFrame(cached_data.get('income', {})),
                'balance': pd.DataFrame(cached_data.get('balance', {})),
                'cash': pd.DataFrame(cached_data.get('cash', {}))
            }

        try:
            stock = yf.Ticker(ticker)
            data = {
                'income': stock.financials,
                'balance': stock.balance_sheet,
                'cash': stock.cashflow
            }
            self._save_to_cache(cache_key, {
                'income': data['income'].to_dict(),
                'balance': data['balance'].to_dict(),
                'cash': data['cash'].to_dict()
            })
            return data
        except Exception as e:
            raise ValueError(f"Failed to fetch financial statements for {ticker}: {str(e)}")

    def get_key_metrics(self, ticker: str) -> pd.DataFrame:
        """Get key metrics for a ticker."""
        cache_key = f"{ticker}_metrics"
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return pd.DataFrame([cached_data])

        try:
            stock = yf.Ticker(ticker)
            metrics = {
                'marketCap': stock.info.get('marketCap'),
                'forwardPE': stock.info.get('forwardPE'),
                'trailingPE': stock.info.get('trailingPE'),
                'priceToBook': stock.info.get('priceToBook'),
                'returnOnEquity': stock.info.get('returnOnEquity'),
                'returnOnAssets': stock.info.get('returnOnAssets'),
                'currentRatio': stock.info.get('currentRatio'),
                'debtToEquity': stock.info.get('debtToEquity'),
                'profitMargins': stock.info.get('profitMargins'),
                'revenueGrowth': stock.info.get('revenueGrowth'),
                'earningsGrowth': stock.info.get('earningsGrowth'),
                'pegRatio': stock.info.get('pegRatio')
            }
            self._save_to_cache(cache_key, metrics)
            return pd.DataFrame([metrics])
        except Exception as e:
            raise ValueError(f"Failed to fetch key metrics for {ticker}: {str(e)}")

    def get_sp500_tickers(self, limit: Optional[int] = None) -> List[str]:
        """Get S&P 500 tickers."""
        cache_key = "sp500_tickers"
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            tickers = cached_data if isinstance(cached_data, list) else []
        else:
            try:
                # Use the S&P 500 ETF (SPY) to get components
                spy = yf.Ticker('SPY')
                tickers = spy.info.get('components', [])
                if not tickers:  # Fallback to a more comprehensive list
                    tickers = [
                        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'BRK-B', 'JNJ', 'V', 'PG', 'JPM',
                        'MA', 'HD', 'NVDA', 'BAC', 'PFE', 'DIS', 'KO', 'NFLX', 'PEP', 'MRK',
                        'ABBV', 'TMO', 'CSCO', 'WMT', 'MCD', 'ABT', 'CVX', 'VZ', 'ADBE', 'CRM',
                        'CMCSA', 'NKE', 'ACN', 'T', 'UNH', 'PYPL', 'INTC', 'IBM', 'ORCL', 'QCOM',
                        'INTU', 'AMGN', 'HON', 'TXN', 'AVGO', 'LOW', 'SBUX', 'GS', 'BA', 'CAT'
                    ]
                self._save_to_cache(cache_key, tickers)
            except Exception as e:
                raise ValueError(f"Failed to fetch S&P 500 tickers: {str(e)}")

        if limit and isinstance(limit, int):
            tickers = tickers[:limit]
        return tickers

    def get_stock_price(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get stock price data for a ticker."""
        cache_key = f"{ticker}_price_{start_date}_{end_date}"
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return pd.DataFrame(cached_data)

        try:
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date)
            if data.empty:
                return pd.DataFrame(columns=['Close', 'Open', 'High', 'Low'])
            self._save_to_cache(cache_key, data.to_dict())
            return data
        except Exception as e:
            raise ValueError(f"Failed to fetch stock price for {ticker}: {str(e)}")