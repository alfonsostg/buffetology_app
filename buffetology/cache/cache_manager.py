import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

class CacheManager:
    def __init__(self, cache_dir: str, expiry_days: int = 7):
        """Initialize the cache manager with directory and expiry settings."""
        self.cache_dir = Path(cache_dir)
        self.expiry_days = expiry_days
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get the path for a cache file."""
        return self.cache_dir / f"{key}.json"

    def _is_expired(self, cache_path: Path) -> bool:
        """Check if a cache file is expired."""
        if not cache_path.exists():
            return True
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime > timedelta(days=self.expiry_days)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from the cache."""
        cache_path = self._get_cache_path(key)
        if not cache_path.exists() or self._is_expired(cache_path):
            return None
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set a value in the cache."""
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'w') as f:
                json.dump(value, f)
        except IOError:
            pass

    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob('*.json'):
            try:
                cache_file.unlink()
            except IOError:
                pass 