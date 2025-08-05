# core/gas_flow_regulator/__init__.py

from .controller import GFRController
from .controller_mock import MockGFRController

__all__ = ["GFRController", "MockGFRController"]
