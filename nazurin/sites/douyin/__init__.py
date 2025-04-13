"""Douyin dynamic site plugin."""

from .api import Douyin
from .config import PRIORITY
from .interface import handle, patterns

__all__ = ["PRIORITY", "Douyin", "handle", "patterns"]
