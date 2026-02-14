"""
Tests for discovery behavior when network interfaces are missing or unavailable.

Ensures the library returns [] instead of crashing when no interfaces exist
or when the network stack (netifaces/ifaddr) is unavailable.
"""
import pytest
from discovery_client import discover
from discovery_client.config import ClientConfig


class TestDiscoverNoInterfaces:
    """discover() must return empty list when no interfaces are available."""

    def test_discover_returns_empty_list_when_no_interfaces(self, monkeypatch):
        """When get_interfaces returns [], discover() returns [] and does not raise."""
        from discovery_client.network import interfaces as iface_mod
        monkeypatch.setattr(iface_mod, "get_interfaces", lambda: [])
        config = ClientConfig(timeout=0.5)
        result = discover(config=config)
        assert result == []

    def test_discover_returns_empty_list_when_import_error(self, monkeypatch):
        """When get_interfaces raises ImportError, discover() returns [] and does not raise."""

        def raise_import_error():
            raise ImportError("No netifaces or ifaddr")

        from discovery_client.network import interfaces as iface_mod
        monkeypatch.setattr(iface_mod, "get_interfaces", raise_import_error)
        config = ClientConfig(timeout=0.5)
        result = discover(config=config)
        assert result == []
