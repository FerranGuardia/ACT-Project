"""
E2E test configuration and fixtures.

Provides network connectivity checks and other E2E-specific setup.
"""

import socket
import pytest


def has_network_connection():
    """
    Check if we have internet connectivity.

    Returns:
        bool: True if internet connection is available, False otherwise
    """
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


@pytest.fixture(autouse=True)
def skip_if_no_network(request):
    """
    Skip network-dependent tests if no internet connection is available.

    This fixture automatically skips any test marked with @pytest.mark.network
    if there's no internet connectivity.
    """
    if request.node.get_closest_marker("network") and not has_network_connection():
        pytest.skip("No internet connection available - skipping network-dependent test")


@pytest.fixture(scope="session")
def network_available():
    """
    Fixture that returns True if network is available, False otherwise.

    Can be used by tests that need to know network status without being skipped.
    """
    return has_network_connection()
