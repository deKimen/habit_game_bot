"""
Main application package for Habit Gamification Bot.

This package contains:
- models: Database models and data structures
- services: Business logic and game mechanics
- db: Database configuration and connection
- core: Application settings and configuration
- utils: Utility functions and helpers
"""

from app.core.config import settings
__all__ = ["settings"]
__version__ = "0.1.0"