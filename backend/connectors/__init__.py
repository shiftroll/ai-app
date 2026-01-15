"""
ERP Connectors for Crafta Revenue Control Room

Supported ERPs:
- QuickBooks Online
- Xero
- NetSuite

All connectors require explicit human approval before posting.
"""

from .quickbooks import QuickBooksConnector
from .xero import XeroConnector
from .netsuite import NetSuiteConnector

__all__ = ["QuickBooksConnector", "XeroConnector", "NetSuiteConnector"]
