import pytest
import os
import yaml
from pathlib import Path
from buffetology.config.config_loader import ConfigLoader

@pytest.fixture
def test_config():
    return {
        'data_provider': {
            'default': 'yahoo',
            'yahoo': {},
            'fmp': {
                'api_key': 'test_key'
            },
            'ft': {
                'username': 'test_user',
                'password': 'test_pass'
            }
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
            'directory': 'test_cache',
            'expiry_days': 7
        },
        'output': {
            'format': 'table',
            'path': 'results'
        }
    }

@pytest.fixture
def test_config_file(tmp_path, test_config):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(test_config, f)
    return str(config_file)

def test_config_loader_initialization(test_config_file):
    """Test that ConfigLoader initializes correctly."""
    loader = ConfigLoader(test_config_file)
    assert loader.config is not None
    assert 'data_provider' in loader.config
    assert 'analysis' in loader.config
    assert 'cache' in loader.config
    assert 'output' in loader.config

def test_get_data_provider_config(test_config_file):
    """Test retrieving data provider configuration."""
    loader = ConfigLoader(test_config_file)
    config = loader.get_data_provider_config()
    assert config['default'] == 'yahoo'
    assert 'yahoo' in config
    assert 'fmp' in config
    assert 'ft' in config

def test_get_analysis_config(test_config_file):
    """Test retrieving analysis configuration."""
    loader = ConfigLoader(test_config_file)
    config = loader.get_analysis_config()
    assert config['sp500_top_n'] == 50
    assert config['min_eps_growth'] == 0.10
    assert config['min_revenue_growth'] == 0.10

def test_get_cache_config(test_config_file):
    """Test retrieving cache configuration."""
    loader = ConfigLoader(test_config_file)
    config = loader.get_cache_config()
    assert config['enabled'] is True
    assert config['directory'] == 'test_cache'
    assert config['expiry_days'] == 7

def test_missing_config_file():
    """Test handling of missing config file."""
    with pytest.raises(FileNotFoundError):
        ConfigLoader("nonexistent.yaml")

def test_invalid_config_format(tmp_path):
    """Test handling of invalid YAML format."""
    config_file = tmp_path / "invalid_config.yaml"
    with open(config_file, 'w') as f:
        f.write("invalid: yaml: content")
    with pytest.raises(ValueError):
        ConfigLoader(str(config_file))

def test_missing_required_sections(tmp_path):
    """Test handling of missing required sections."""
    config_file = tmp_path / "incomplete_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump({'data_provider': {}}, f)
    with pytest.raises(ValueError):
        ConfigLoader(str(config_file)) 