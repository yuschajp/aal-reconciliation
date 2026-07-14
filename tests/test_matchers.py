import pytest
from datetime import date
from aal_reconciliation.models import Trade
from aal_reconciliation.matchers import SwapsMatcher, CDSMatcher


class TestSwapsMatcher:
    """Test suite for SwapsMatcher."""
    
    def test_exact_match_no_variance(self):
        """Two identical swaps should match with no breaks."""
        trade_a = Trade(
            internal_id="XX-2026-001",
            system_source="IMAGINE_TS",
            counterparty="JPM",
            asset_class="SWAPS",
            effective_date=date(2026, 7, 1),
            notional=50_000_000.0,
            fixed_rate=0.035,
            settlement_date=date(2026, 7, 3),
        )
        trade_b = Trade(
            internal_id="XX-2026-001",
            system_source="NORTHSTAR",
            counterparty="JPM",
            asset_class="SWAPS",
            effective_date=date(2026, 7, 1),
            notional=50_000_000.0,
            fixed_rate=0.035,
            settlement_date=date(2026, 7, 3),
        )
        
        matcher = SwapsMatcher()
        matched, breaks = matcher.match_trades([trade_a], [trade_b])
        
        assert len(matched) == 1
        assert len(breaks) == 0
    
    def test_notional_variance_high(self):
        """Notional mismatch >1% should flag HIGH severity."""
        trade_a = Trade(
            internal_id="XX-2026-001",
            system_source="IMAGINE_TS",
            counterparty="JPM",
            asset_class="SWAPS",
            effective_date=date(2026, 7, 1),
            notional=50_000_000.0,
            fixed_rate=0.035,
        )
        trade_b = Trade(
            internal_id="XX-2026-001",
            system_source="NORTHSTAR",
            counterparty="JPM",
            asset_class="SWAPS",
            effective_date=date(2026, 7, 1),
            notional=50_600_000.0,  # 1.2% higher
            fixed_rate=0.035,
        )
        
        matcher = SwapsMatcher(tolerance_bps=5)
        matched, breaks = matcher.match_trades([trade_a], [trade_b])
        
        assert len(matched) == 1
        assert len(breaks) == 1
        assert breaks[0].break_type == "DATA_VARIANCE"
        assert breaks[0].field_name == "NOTIONAL"
        assert breaks[0].severity == "HIGH"
    
    def test_fixed_rate_variance_low(self):
        """Fixed rate diff <10bps should flag LOW severity."""
        trade_a = Trade(
            internal_id="XX-2026-001",
            system_source="IMAGINE_TS",
            counterparty="JPM",
            asset_class="SWAPS",
            effective_date=date(2026, 7, 1),
            notional=50_000_000.0,
            fixed_rate=0.0350,
        )
        trade_b = Trade(
            internal_id="XX-2026-001",
            system_source="NORTHSTAR",
            counterparty="JPM",
            asset_class="SWAPS",
            effective_date=date(2026, 7, 1),
            notional=50_000_000.0,
            fixed_rate=0.0351,  # 1bp higher
        )
        
        matcher = SwapsMatcher()
        matched, breaks = matcher.match_trades([trade_a], [trade_b])
        
        assert len(matched) == 1
        assert len(breaks) == 1
        assert breaks[0].break_type == "DATA_VARIANCE"
        assert breaks[0].field_name == "FIXED_RATE"
        assert breaks[0].severity == "LOW"
    
    def test_unmatched_in_system_a(self):
        """Trade in system A but not B should flag UNMATCHED_SYSTEM_A."""
        trade_a = Trade(
            internal_id="XX-2026-001",
            system_source="IMAGINE_TS",
            counterparty="JPM",
            asset_class="SWAPS",
            effective_date=date(2026, 7, 1),
            notional=50_000_000.0,
            fixed_rate=0.035,
        )
        
        matcher = SwapsMatcher()
        matched, breaks = matcher.match_trades([trade_a], [])
        
        assert len(matched) == 0
        assert len(breaks) == 1
        assert breaks[0].break_type == "UNMATCHED_SYSTEM_A"
    
    def test_unmatched_in_system_b(self):
        """Trade in system B but not A should flag UNMATCHED_SYSTEM_B."""
        trade_b = Trade(
            internal_id="XX-2026-001",
            system_source="NORTHSTAR",
            counterparty="JPM",
            asset_class="SWAPS",
            effective_date=date(2026, 7, 1),
            notional=50_000_000.0,
            fixed_rate=0.035,
        )
        
        matcher = SwapsMatcher()
        matched, breaks = matcher.match_trades([], [trade_b])
        
        assert len(matched) == 0
        assert len(breaks) == 1
        assert breaks[0].break_type == "UNMATCHED_SYSTEM_B"


class TestCDSMatcher:
    """Test suite for CDSMatcher."""
    
    def test_exact_match_no_variance(self):
        """Two identical CDS should match with no breaks."""
        trade_a = Trade(
            internal_id="CD-2026-001",
            system_source="IMAGINE_TS",
            counterparty="JPM",
            asset_class="CDS",
            effective_date=date(2026, 7, 1),
            notional=10_000_000.0,
            coupon=0.01,
            ref_entity="ACME Corp",
            settlement_date=date(2026, 7, 3),
        )
        trade_b = Trade(
            internal_id="CD-2026-001",
            system_source="NORTHSTAR",
            counterparty="JPM",
            asset_class="CDS",
            effective_date=date(2026, 7, 1),
            notional=10_000_000.0,
            coupon=0.01,
            ref_entity="ACME Corp",
            settlement_date=date(2026, 7, 3),
        )
        
        matcher = CDSMatcher()
        matched, breaks = matcher.match_trades([trade_a], [trade_b])
        
        assert len(matched) == 1
        assert len(breaks) == 0
    
    def test_coupon_variance_high(self):
        """Coupon diff >25bps should flag HIGH severity."""
        trade_a = Trade(
            internal_id="CD-2026-001",
            system_source="IMAGINE_TS",
            counterparty="JPM",
            asset_class="CDS",
            effective_date=date(2026, 7, 1),
            notional=10_000_000.0,
            coupon=0.0100,
            ref_entity="ACME Corp",
        )
        trade_b = Trade(
            internal_id="CD-2026-001",
            system_source="NORTHSTAR",
            counterparty="JPM",
            asset_class="CDS",
            effective_date=date(2026, 7, 1),
            notional=10_000_000.0,
            coupon=0.0130,  # 30bps higher
            ref_entity="ACME Corp",
        )
        
        matcher = CDSMatcher()
        matched, breaks = matcher.match_trades([trade_a], [trade_b])
        
        assert len(matched) == 1
        assert len(breaks) == 1
        assert breaks[0].break_type == "DATA_VARIANCE"
        assert breaks[0].field_name == "COUPON"
        assert breaks[0].severity == "HIGH"
    
    def test_recovery_assumption_variance(self):
        """Recovery assumption diff should be detected."""
        trade_a = Trade(
            internal_id="CD-2026-001",
            system_source="IMAGINE_TS",
            counterparty="JPM",
            asset_class="CDS",
            effective_date=date(2026, 7, 1),
            notional=10_000_000.0,
            coupon=0.01,
            ref_entity="ACME Corp",
            recovery_assumption=0.40,
        )
        trade_b = Trade(
            internal_id="CD-2026-001",
            system_source="NORTHSTAR",
            counterparty="JPM",
            asset_class="CDS",
            effective_date=date(2026, 7, 1),
            notional=10_000_000.0,
            coupon=0.01,
            ref_entity="ACME Corp",
            recovery_assumption=0.30,  # 10% diff
        )
        
        matcher = CDSMatcher()
        matched, breaks = matcher.match_trades([trade_a], [trade_b])
        
        assert len(matched) == 1
        assert len(breaks) == 1
        assert breaks[0].break_type == "DATA_VARIANCE"
        assert breaks[0].field_name == "RECOVERY_ASSUMPTION"
        assert breaks[0].severity == "MEDIUM"
