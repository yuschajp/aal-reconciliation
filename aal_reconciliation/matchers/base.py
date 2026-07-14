from abc import ABC, abstractmethod
from aal_reconciliation.models import Trade, BreakRecord


class BaseMatcher(ABC):
    """Abstract matcher for asset-class-specific reconciliation logic."""
    
    def __init__(self, tolerance_bps: float = 5):
        """
        Args:
            tolerance_bps: Notional tolerance in basis points (default 5 bps).
        """
        self.tolerance_bps = tolerance_bps
    
    @abstractmethod
    def match_trades(self, system_a: list[Trade], system_b: list[Trade]) -> tuple[list[tuple[Trade, Trade]], list[BreakRecord]]:
        """
        Match trades across two systems.
        
        Returns:
            (matched_pairs, break_records)
        """
        pass
    
    @abstractmethod
    def _check_variances(self, trade_a: Trade, trade_b: Trade) -> list[BreakRecord]:
        """Check for data variances between two matched trades."""
        pass
