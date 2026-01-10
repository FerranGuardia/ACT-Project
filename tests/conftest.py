"""
Root conftest for all tests - provides circuit breaker isolation fixtures.

This file contains shared fixtures that ensure proper test isolation,
particularly for circuit breaker state management.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import shared circuit breaker fixtures
from tests._circuit_breaker_fixtures import (
    reset_circuit_breaker,
    reset_all_circuit_breakers,
    fresh_circuit_breaker,
    isolated_edge_provider
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    import shutil
    import tempfile
    
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    
    # Cleanup
    try:
        shutil.rmtree(temp_path, ignore_errors=True)
    except:
        pass  # Ignore cleanup errors
