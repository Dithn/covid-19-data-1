"""Add here processes for individual countries.

All modules should have a main function that returns a dataframe with the data and a metadata dictionary with info
regarding sources.
"""
import pkgutil


__all__ = []


for loader, module_name, _is_pkg in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
