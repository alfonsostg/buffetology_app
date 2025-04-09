from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime, timedelta
import os
import yaml
from typing import Dict, List, Optional, Union, Any
from buffetology.config.config_loader import ConfigLoader
from buffetology.cache.cache_manager import CacheManager

class BaseDataFetcher(ABC):
    def __init__(self, cache_manager: Optional[CacheManager] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize the base fetcher.
        
        Args:
            cache_manager: Optional cache manager instance
            config: Optional configuration dictionary
        """
        self.config = config or ConfigLoader().config
        self.cache_manager = cache_manager or CacheManager(
            enabled=self.config['cache']['enabled'],
            cache_dir=self.config['cache']['directory'],
            expiry_days=self.config['cache']['expiry_days']
        )
        self._ensure_cache_directory()
    
    def _ensure_cache_directory(self):
        """Ensure the cache directory exists."""
        os.makedirs(self.config['cache']['directory'], exist_ok=True)
    
    def _get_cache_path(self, ticker: str, data_type: str) -> str:
        """Get the cache file path for a specific ticker and data type."""
        return os.path.join(self.config['cache']['directory'], f"{ticker}_{data_type}.csv")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cached data is still valid."""
        if not os.path.exists(cache_path):
            return False
        
        cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))
        return cache_age.days < self.config['cache']['expiry_days']
    
    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """Load data from cache if available and valid."""
        if not self.config['cache']['enabled']:
            return None
            
        try:
            return self.cache_manager.get(cache_key)
        except Exception:
            return None
    
    def _save_to_cache(self, cache_key: str, data: Any):
        """Save data to cache."""
        if not self.config['cache']['enabled']:
            return
            
        try:
            self.cache_manager.set(cache_key, data)
        except Exception:
            pass
    
    def _get_provider_config(self) -> Dict[str, Any]:
        """Get provider-specific configuration."""
        return self.config['data_provider']
    
    @abstractmethod
    def get_financial_statements(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """Fetch financial statements (income statement, balance sheet, cash flow)"""
        pass
    
    @abstractmethod
    def get_key_metrics(self, ticker: str) -> pd.DataFrame:
        """Fetch key financial metrics"""
        pass
    
    @abstractmethod
    def get_stock_price(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical stock prices"""
        pass
    
    @abstractmethod
    def get_sp500_tickers(self, limit: int) -> List[str]:
        """Fetch list of S&P 500 tickers"""
        pass 