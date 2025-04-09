from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from buffetology.data_fetchers.base_fetcher import BaseDataFetcher
from buffetology.config.config_loader import ConfigLoader
import yaml

class BuffetologyAnalyzer:
    def __init__(self, data_fetcher: BaseDataFetcher, config: ConfigLoader):
        """Initialize the analyzer with a data fetcher and configuration."""
        self.data_fetcher = data_fetcher
        self.config = config
        self.results = {}

    def analyze_ticker(self, ticker: str) -> Dict[str, Any]:
        """Analyze a single ticker and return a dictionary of scores."""
        try:
            # Get financial data
            metrics = self.data_fetcher.get_key_metrics(ticker)
            
            # Check if we have sufficient data
            required_metrics = [
                'debtToEquity', 'currentRatio', 'returnOnEquity', 'profitMargins',
                'trailingPE', 'priceToBook', 'pegRatio', 'marketCap',
                'revenueGrowth', 'earningsGrowth'
            ]
            
            if metrics.empty or not all(metric in metrics.columns for metric in required_metrics):
                return {
                    'ticker': ticker,
                    'quality_score': 0,
                    'value_score': 0,
                    'growth_score': 0,
                    'overall_score': 0,
                    'recommendation': 'Not enough data'
                }
            
            # Calculate scores
            quality_score = self._calculate_quality_score(metrics)
            value_score = self._calculate_value_score(metrics)
            growth_score = self._calculate_growth_score(metrics)
            
            # Calculate overall score (weighted average)
            overall_score = (quality_score * 0.4 + value_score * 0.3 + growth_score * 0.3)
            
            # Determine recommendation
            recommendation = self._get_recommendation(overall_score)
            
            return {
                'ticker': ticker,
                'quality_score': quality_score,
                'value_score': value_score,
                'growth_score': growth_score,
                'overall_score': overall_score,
                'recommendation': recommendation
            }
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {str(e)}")
            return {
                'ticker': ticker,
                'quality_score': 0,
                'value_score': 0,
                'growth_score': 0,
                'overall_score': 0,
                'recommendation': 'Error'
            }

    def _get_recommendation(self, overall_score: float) -> str:
        """Get recommendation based on overall score."""
        if overall_score >= 80:
            return 'Strong Buy'
        elif overall_score >= 60:
            return 'Buy'
        elif overall_score >= 40:
            return 'Hold'
        elif overall_score >= 30:
            return 'Sell'
        else:
            return 'Strong Sell'

    def analyze_stocks(self, tickers: List[str]) -> pd.DataFrame:
        """Analyze multiple stocks and return results as a DataFrame."""
        results = []
        for ticker in tickers:
            result = self.analyze_ticker(ticker)
            results.append(result)
            
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Sort by overall score
        results_df = results_df.sort_values('overall_score', ascending=False)
        
        return results_df

    def analyze_sp500(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Analyze top S&P 500 stocks."""
        if limit is None:
            limit = self.config.get_analysis_config().get('sp500_top_n', 50)
        
        tickers = self.data_fetcher.get_sp500_tickers()[:limit]
        return self.analyze_stocks(tickers)

    def _calculate_quality_score(self, metrics: pd.DataFrame) -> float:
        """Calculate quality score based on financial metrics."""
        score = 0
        max_score = 100
        analysis_config = self.config.get_analysis_config()

        if metrics.empty:
            return 0

        # Check debt levels
        debt_to_equity = metrics['debtToEquity'].iloc[0] if 'debtToEquity' in metrics else None
        if debt_to_equity is not None and debt_to_equity > 0:
            if debt_to_equity <= analysis_config['debt_to_equity_threshold']:
                score += 20

        # Check current ratio
        current_ratio = metrics['currentRatio'].iloc[0] if 'currentRatio' in metrics else None
        if current_ratio is not None and current_ratio > 0:
            if current_ratio >= analysis_config['min_current_ratio']:
                score += 20

        # Check profitability
        roe = metrics['returnOnEquity'].iloc[0] if 'returnOnEquity' in metrics else None
        if roe is not None and roe > 0:
            if roe >= analysis_config['min_roe']:
                score += 20

        # Check profit margins
        profit_margins = metrics['profitMargins'].iloc[0] if 'profitMargins' in metrics else None
        if profit_margins is not None and profit_margins > 0:
            if profit_margins >= analysis_config['min_net_margin']:
                score += 20

        # Check market cap
        market_cap = metrics['marketCap'].iloc[0] if 'marketCap' in metrics else None
        if market_cap is not None and market_cap > 0:
            if market_cap >= analysis_config['min_market_cap']:
                score += 20

        return min(score, max_score)

    def _calculate_value_score(self, metrics: pd.DataFrame) -> float:
        """Calculate value score based on financial metrics."""
        score = 0
        max_score = 100
        analysis_config = self.config.get_analysis_config()

        if metrics.empty:
            return 0

        # Check P/E ratio
        pe_ratio = metrics['trailingPE'].iloc[0] if 'trailingPE' in metrics else None
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio <= analysis_config['max_pe_ratio']:
                score += 25

        # Check P/B ratio
        pb_ratio = metrics['priceToBook'].iloc[0] if 'priceToBook' in metrics else None
        if pb_ratio is not None and pb_ratio > 0:
            if pb_ratio <= analysis_config['max_pb_ratio']:
                score += 25

        # Check PEG ratio
        peg_ratio = metrics['pegRatio'].iloc[0] if 'pegRatio' in metrics else None
        if peg_ratio is not None and peg_ratio > 0:
            if peg_ratio <= analysis_config['max_peg_ratio']:
                score += 25

        # Check market cap
        market_cap = metrics['marketCap'].iloc[0] if 'marketCap' in metrics else None
        if market_cap is not None and market_cap > 0:
            if market_cap >= analysis_config['min_market_cap']:
                score += 25

        return min(score, max_score)

    def _calculate_growth_score(self, metrics: pd.DataFrame) -> float:
        """Calculate growth score based on financial metrics."""
        score = 0
        max_score = 100
        analysis_config = self.config.get_analysis_config()

        if metrics.empty:
            return 0

        # Check revenue growth
        revenue_growth = metrics['revenueGrowth'].iloc[0] if 'revenueGrowth' in metrics else None
        if revenue_growth is not None and revenue_growth > 0:
            if revenue_growth >= analysis_config['min_revenue_growth']:
                score += 33.33

        # Check earnings growth
        earnings_growth = metrics['earningsGrowth'].iloc[0] if 'earningsGrowth' in metrics else None
        if earnings_growth is not None and earnings_growth > 0:
            if earnings_growth >= analysis_config['min_earnings_growth']:
                score += 33.33

        # Check free cash flow growth (not directly available from Yahoo Finance)
        # We'll use earnings growth as a proxy
        if earnings_growth is not None and earnings_growth > 0:
            if earnings_growth >= analysis_config['min_earnings_growth']:
                score += 33.33

        return min(score, max_score)

    def _analyze_debt(self, metrics: pd.DataFrame) -> float:
        """Analyze debt levels and return a score."""
        score = 0
        max_score = 100
        analysis_config = self.config.get_analysis_config()
        
        if metrics.empty:
            return 0
            
        debt_to_equity = metrics['debtToEquity'].iloc[0] if 'debtToEquity' in metrics else None
        if debt_to_equity is not None and debt_to_equity > 0:
            if debt_to_equity <= analysis_config['debt_to_equity_threshold']:
                score += 100
        
        return min(score, max_score)

    def _analyze_profitability(self, metrics: pd.DataFrame) -> float:
        """Analyze profitability metrics and return a score."""
        score = 0
        max_score = 100
        analysis_config = self.config.get_analysis_config()
        
        if metrics.empty:
            return 0
            
        roe = metrics['returnOnEquity'].iloc[0] if 'returnOnEquity' in metrics else None
        profit_margin = metrics['profitMargins'].iloc[0] if 'profitMargins' in metrics else None
        
        if roe is not None and roe > 0:
            if roe >= analysis_config['min_roe']:
                score += 50
                
        if profit_margin is not None and profit_margin > 0:
            if profit_margin >= analysis_config['min_profit_margin']:
                score += 50
        
        return min(score, max_score)

    def _analyze_eps_growth(self, metrics: pd.DataFrame) -> float:
        """Analyze EPS growth and return a score."""
        score = 0
        max_score = 100
        analysis_config = self.config.get_analysis_config()
        
        if metrics.empty:
            return 0
            
        earnings_growth = metrics['earningsGrowth'].iloc[0] if 'earningsGrowth' in metrics else None
        if earnings_growth is not None and earnings_growth > 0:
            if earnings_growth >= analysis_config['min_earnings_growth']:
                score += 100
        
        return min(score, max_score) 