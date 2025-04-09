import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import os

class ConfigLoader:
    def __init__(self, config_input: Optional[Union[str, Dict[str, Any]]] = None):
        """Initialize the configuration loader.
        
        Args:
            config_input: Either a path to a YAML config file or a dictionary with configuration
        """
        self.config_path = config_input if isinstance(config_input, str) else None
        self.config = (self._load_config() if isinstance(config_input, str) 
                      else config_input if isinstance(config_input, dict)
                      else self._load_default_config())
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        default_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "config", 
            "config.yaml"
        )
        try:
            with open(default_config_path, 'r') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError):
            return {
                'data_provider': {
                    'default': 'yahoo',
                    'yahoo': {}
                },
                'analysis': {
                    'sp500_top_n': 50,
                    'min_eps_growth': 0.10,
                    'min_revenue_growth': 0.10,
                    'years_of_history': 5,
                    'debt_to_equity_threshold': 0.5,
                    'min_current_ratio': 1.5,
                    'min_roe': 0.15
                },
                'cache': {
                    'enabled': True,
                    'directory': 'cache',
                    'expiry_days': 7
                },
                'output': {
                    'format': 'table',
                    'path': 'results'
                }
            }

    def _validate_config(self) -> None:
        """Validate the configuration file has all required fields."""
        if not isinstance(self.config, dict):
            raise ValueError("Configuration must be a dictionary")

        required_sections = ['data_provider', 'analysis', 'cache', 'output']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required section '{section}' in config")

        # Validate data provider configuration
        provider = self.config['data_provider']
        if 'default' not in provider:
            raise ValueError("Missing default data provider in config")
        if provider['default'] not in ['yahoo', 'fmp', 'ft']:
            raise ValueError("Invalid default data provider specified")

        # Validate analysis configuration
        analysis = self.config['analysis']
        required_analysis_fields = [
            'sp500_top_n', 'min_eps_growth', 'min_revenue_growth',
            'years_of_history', 'debt_to_equity_threshold',
            'min_current_ratio', 'min_roe'
        ]
        for field in required_analysis_fields:
            if field not in analysis:
                raise ValueError(f"Missing required analysis field '{field}' in config")

        # Validate cache configuration
        cache = self.config['cache']
        required_cache_fields = ['enabled', 'directory', 'expiry_days']
        for field in required_cache_fields:
            if field not in cache:
                raise ValueError(f"Missing required cache field '{field}' in config")

    def get_data_provider_config(self) -> Dict[str, Any]:
        """Get data provider configuration."""
        return self.config['data_provider']

    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis configuration."""
        return self.config['analysis']

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return self.config['cache']

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self.config['output']

    def get_provider_credentials(self, provider: str) -> Dict[str, str]:
        """Get credentials for specific provider."""
        provider_config = self.config['data_provider'].get(provider, {})
        if provider == 'fmp':
            return {'api_key': provider_config.get('api_key', '')}
        elif provider == 'ft':
            return {
                'username': provider_config.get('username', ''),
                'password': provider_config.get('password', '')
            }
        return {} 