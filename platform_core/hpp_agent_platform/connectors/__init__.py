"""Connector framework for the HPP suite — fixture (offline) and live adapters."""
from .base import Connector, FixtureBackedConnector
from .factory import get_connector

__all__ = ["Connector", "FixtureBackedConnector", "get_connector"]
