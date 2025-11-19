"""Pytest configuration for all tests.

This module sets up global test configuration including environment variables
that need to be set before any application code is imported.
"""

import os

# Set required environment variables for testing
# These must be set before any application code imports settings
os.environ.setdefault("OPENROUTER_API_KEY", "test-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
