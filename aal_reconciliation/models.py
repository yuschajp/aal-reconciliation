from pydantic import BaseModel
from typing import Optional
from datetime import date


class Trade(BaseModel):
    """Standardized trade object across all systems."""
    internal_id: str           # Your common ID
    system_source: str         # IMAGINE_TS, NORTHSTAR, SSC
    counterparty: str
    asset_class: str           # SWAPS, CDS
    effective_date: date
    notional: float
    
    # Swap-specific
    fixed_rate: Optional[float] = None
    float_index: Optional[str] = None
    settlement_date: Optional[date] = None
    
    # CDS-specific
    coupon: Optional[float] = None
    ref_entity: Optional[str] = None
    recovery_assumption: Optional[float] = None
    
    # Metadata
    raw_row: Optional[dict] = None  # Keep original CSV row for debugging


class BreakRecord(BaseModel):
    """Represents a single reconciliation break."""
    break_type: str  # UNMATCHED_SYSTEM_A, UNMATCHED_SYSTEM_B, DATA_VARIANCE
    trade_id: str
    system_a: Optional[str] = None
    system_b: Optional[str] = None
    field_name: Optional[str] = None
    value_a: Optional[str] = None
    value_b: Optional[str] = None
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    notes: str


class ReconciliationReport(BaseModel):
    """Final output report."""
    reconciliation_date: str
    asset_class: str
    summary: dict  # counts
    breaks: list[BreakRecord]
