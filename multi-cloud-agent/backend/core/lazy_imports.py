"""Lazy import utilities for memory optimization.

This module provides utilities to defer heavy imports until they're actually needed,
reducing startup memory usage and improving application startup time.
"""

import importlib
import logging
import os
import subprocess
import sys
from typing import Any, Dict, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

class LazyImport:
    """A lazy import wrapper that defers module loading until first access."""
    
    def __init__(self, module_name: str, attribute: Optional[str] = None):
        self.module_name = module_name
        self.attribute = attribute
        self._module = None
        self._loaded = False
    
    def _load_module(self):
        """Load the module if not already loaded."""
        if not self._loaded:
            try:
                self._module = importlib.import_module(self.module_name)
                self._loaded = True
                logger.debug(f"Lazy loaded module: {self.module_name}")
            except ImportError as e:
                logger.error(f"Failed to lazy load {self.module_name}: {e}")
                raise
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute from the lazily loaded module."""
        self._load_module()
        if self.attribute:
            # If we're wrapping a specific attribute, get it first
            attr = getattr(self._module, self.attribute)
            return getattr(attr, name)
        return getattr(self._module, name)
    
    def __call__(self, *args, **kwargs) -> Any:
        """Make the lazy import callable if the target is callable."""
        self._load_module()
        if self.attribute:
            target = getattr(self._module, self.attribute)
        else:
            target = self._module
        return target(*args, **kwargs)

class LazyMLImport(LazyImport):
    """Specialized lazy import for ML libraries with auto-installation."""
    
    def __init__(self, module_name: str, package_name: str = None, attribute: Optional[str] = None):
        super().__init__(module_name, attribute)
        self.package_name = package_name or module_name
        self._install_attempted = False
    
    def _install_package(self):
        """Install the package if not available."""
        if self._install_attempted:
            return
        
        self._install_attempted = True
        logger.warning(f"Installing {self.package_name} on-demand for memory optimization")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                self.package_name, "--no-cache-dir"
            ])
            logger.info(f"Successfully installed {self.package_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {self.package_name}: {e}")
            raise ImportError(f"Could not install {self.package_name}")
    
    def _load_module(self):
        """Load the module, installing if necessary."""
        if not self._loaded:
            try:
                self._module = importlib.import_module(self.module_name)
                self._loaded = True
                logger.debug(f"Lazy loaded ML module: {self.module_name}")
            except ImportError:
                # Try to install and load again
                self._install_package()
                try:
                    self._module = importlib.import_module(self.module_name)
                    self._loaded = True
                    logger.debug(f"Lazy loaded ML module after installation: {self.module_name}")
                except ImportError as e:
                    logger.error(f"Failed to lazy load {self.module_name} even after installation: {e}")
                    raise
    
    @property
    def is_loaded(self) -> bool:
        """Check if the module has been loaded."""
        return self._loaded
    
    def get_module(self) -> Any:
        """Get the actual module (forces loading)."""
        self._load_module()
        return self._module

class LazyRegistry:
    """Registry for managing lazy imports across the application."""
    
    def __init__(self):
        self._registry: Dict[str, LazyImport] = {}
        self._load_stats: Dict[str, bool] = {}
    
    def register(self, name: str, module_name: str, attribute: Optional[str] = None) -> LazyImport:
        """Register a lazy import."""
        lazy_import = LazyImport(module_name, attribute)
        self._registry[name] = lazy_import
        self._load_stats[name] = False
        logger.debug(f"Registered lazy import: {name} -> {module_name}")
        return lazy_import
    
    def get(self, name: str) -> Optional[LazyImport]:
        """Get a registered lazy import."""
        return self._registry.get(name)
    
    def force_load(self, name: str) -> bool:
        """Force load a specific lazy import."""
        lazy_import = self._registry.get(name)
        if lazy_import:
            try:
                lazy_import._load_module()
                self._load_stats[name] = True
                return True
            except Exception as e:
                logger.error(f"Failed to force load {name}: {e}")
                return False
        return False
    
    def force_load_all(self) -> Dict[str, bool]:
        """Force load all registered lazy imports."""
        results = {}
        for name in self._registry:
            results[name] = self.force_load(name)
        return results
    
    def get_load_stats(self) -> Dict[str, bool]:
        """Get loading statistics for all registered imports."""
        stats = {}
        for name, lazy_import in self._registry.items():
            stats[name] = lazy_import.is_loaded
        return stats
    
    def clear(self):
        """Clear all registered lazy imports."""
        self._registry.clear()
        self._load_stats.clear()

# Global lazy import registry
lazy_registry = LazyRegistry()

def lazy_import(module_name: str, attribute: Optional[str] = None) -> LazyImport:
    """Create a lazy import for a module or module attribute.
    
    Args:
        module_name: The name of the module to import
        attribute: Optional specific attribute to import from the module
    
    Returns:
        LazyImport: A lazy import wrapper
    
    Example:
        # Lazy import entire module
        selenium = lazy_import('selenium')
        
        # Lazy import specific attribute
        webdriver = lazy_import('selenium', 'webdriver')
    """
    return LazyImport(module_name, attribute)

def conditional_import(condition_func: Callable[[], bool]):
    """Decorator to conditionally import modules based on runtime conditions.
    
    Args:
        condition_func: Function that returns True if import should proceed
    
    Example:
        @conditional_import(lambda: settings.ENABLE_BROWSER_AUTOMATION)
        def get_selenium():
            import selenium
            return selenium
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if condition_func():
                return func(*args, **kwargs)
            else:
                logger.debug(f"Skipping conditional import for {func.__name__}")
                return None
        return wrapper
    return decorator

# Pre-register common heavy imports for the application
def register_common_lazy_imports():
    """Register commonly used heavy imports as lazy imports."""
    
    # Browser automation imports
    lazy_registry.register('selenium', 'selenium')
    lazy_registry.register('webdriver', 'selenium.webdriver')
    lazy_registry.register('chrome_options', 'selenium.webdriver.chrome.options', 'Options')
    lazy_registry.register('firefox_options', 'selenium.webdriver.firefox.options', 'Options')
    
    # Machine learning imports
    lazy_registry.register('torch', 'torch')
    lazy_registry.register('transformers', 'transformers')
    lazy_registry.register('sentence_transformers', 'sentence_transformers')
    
    # Data processing imports
    lazy_registry.register('pandas', 'pandas')
    lazy_registry.register('numpy', 'numpy')
    
    # Web scraping imports
    lazy_registry.register('beautifulsoup', 'bs4', 'BeautifulSoup')
    lazy_registry.register('requests', 'requests')
    
    # Cloud SDK imports
    lazy_registry.register('boto3', 'boto3')
    lazy_registry.register('google_cloud', 'google.cloud')
    lazy_registry.register('azure_sdk', 'azure')
    
    logger.info("Registered common lazy imports for memory optimization")

# Initialize common lazy imports
register_common_lazy_imports()

# ML-specific lazy imports with auto-installation
_ml_lazy_imports = {
    'torch': LazyMLImport('torch', 'torch>=1.9.0'),
    'transformers': LazyMLImport('transformers', 'transformers>=4.20.0'),
    'sentence_transformers': LazyMLImport('sentence_transformers', 'sentence-transformers>=2.2.0'),
    'numpy': LazyMLImport('numpy', 'numpy>=1.21.0'),
    'scipy': LazyMLImport('scipy', 'scipy>=1.7.0'),
    'sklearn': LazyMLImport('sklearn', 'scikit-learn>=1.0.0'),
    'pandas': LazyMLImport('pandas', 'pandas>=1.3.0'),
    'matplotlib': LazyMLImport('matplotlib', 'matplotlib>=3.4.0'),
    'seaborn': LazyMLImport('seaborn', 'seaborn>=0.11.0'),
    'plotly': LazyMLImport('plotly', 'plotly>=5.0.0'),
}

# Common lazy imports for other heavy modules
_lazy_imports = {
    'requests': LazyImport('requests'),
    'beautifulsoup4': LazyImport('bs4', 'beautifulsoup4'),
    'lxml': LazyImport('lxml'),
    'selenium': LazyImport('selenium'),
}

def get_lazy_import(module_name: str, use_ml_import: bool = False) -> LazyImport:
    """Get a lazy import for a module.
    
    Args:
        module_name: Name of the module to import lazily
        use_ml_import: Whether to use ML lazy import with auto-installation
        
    Returns:
        LazyImport instance for the module
    """
    if use_ml_import and module_name in _ml_lazy_imports:
        return _ml_lazy_imports[module_name]
    elif module_name in _lazy_imports:
        return _lazy_imports[module_name]
    elif use_ml_import:
        return LazyMLImport(module_name)
    return LazyImport(module_name)

def lazy_import_decorator(module_names: list, use_ml_import: bool = False):
    """Decorator to lazily import modules for a function.
    
    Args:
        module_names: List of module names to import lazily
        use_ml_import: Whether to use ML lazy import with auto-installation
        
    Returns:
        Decorated function with lazy imports available
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Make lazy imports available in function scope
            for module_name in module_names:
                lazy_module = get_lazy_import(module_name, use_ml_import)
                # Force loading of the module
                lazy_module._load_module()
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Pre-configured lazy imports for common heavy ML modules
# These will auto-install if needed
torch = get_lazy_import('torch', use_ml_import=True)
transformers = get_lazy_import('transformers', use_ml_import=True)
sentence_transformers = get_lazy_import('sentence_transformers', use_ml_import=True)
numpy = get_lazy_import('numpy', use_ml_import=True)
scipy = get_lazy_import('scipy', use_ml_import=True)
sklearn = get_lazy_import('sklearn', use_ml_import=True)
pandas = get_lazy_import('pandas', use_ml_import=True)
matplotlib = get_lazy_import('matplotlib', use_ml_import=True)
seaborn = get_lazy_import('seaborn', use_ml_import=True)
plotly = get_lazy_import('plotly', use_ml_import=True)