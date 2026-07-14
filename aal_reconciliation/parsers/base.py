from abc import ABC, abstractmethod
import pandas as pd
from aal_reconciliation.models import Trade


class BaseParser(ABC):
    """Abstract parser to convert CSV from each system into standardized Trade objects."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df = pd.read_csv(filepath)
    
    @abstractmethod
    def parse(self) -> list[Trade]:
        """Convert CSV rows to Trade objects."""
        pass
