"""Backward-compatible shim for historical typo module name.

This module exists to support deployments that still import ``data_loder``
instead of ``data_loader``.
"""

from data_loader import DataRequest, load_ohlcv_data

__all__ = ["DataRequest", "load_ohlcv_data"]
