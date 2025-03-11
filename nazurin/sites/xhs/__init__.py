"""Xhs dynamic site plugin."""

from .xhs import Xhs
from .config import PRIORITY
from .interface import handle, patterns

__all__ = ["PRIORITY", "Xhs", "handle", "patterns"]
