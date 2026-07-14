from aal_reconciliation.matchers.base import BaseMatcher
from aal_reconciliation.models import Trade, BreakRecord


class CDSMatcher(BaseMatcher):
    """CDS-specific reconciliation logic."""
    
    def match_trades(self, system_a: list[Trade], system_b: list[Trade]) -> tuple[list[tuple[Trade, Trade]], list[BreakRecord]]:
        """Match CDS trades across two systems."""
        matched = []
        breaks = []
        unmatched_b = {t.internal_id: t for t in system_b}
        
        for trade_a in system_a:
            # Primary match: exact internal_id
            match_b = next((t for t in system_b if t.internal_id == trade_a.internal_id), None)
            
            if match_b:
                matched.append((trade_a, match_b))
                if match_b.internal_id in unmatched_b:
                    del unmatched_b[match_b.internal_id]
                
                # Check for data variances
                variances = self._check_variances(trade_a, match_b)
                breaks.extend(variances)
            else:
                # No match found in system B
                breaks.append(BreakRecord(
                    break_type="UNMATCHED_SYSTEM_A",
                    trade_id=trade_a.internal_id,
                    system_a=trade_a.system_source,
                    severity="HIGH",
                    notes=f"Trade {trade_a.internal_id} ({trade_a.ref_entity}, {trade_a.notional:,.0f}) in {trade_a.system_source} not found in comparison system."
                ))
        
        # Unmatched in System B
        for trade_id, trade_b in unmatched_b.items():
            breaks.append(BreakRecord(
                break_type="UNMATCHED_SYSTEM_B",
                trade_id=trade_id,
                system_b=trade_b.system_source,
                severity="HIGH",
                notes=f"Trade {trade_id} ({trade_b.ref_entity}, {trade_b.notional:,.0f}) in {trade_b.system_source} not found in comparison system."
            ))
        
        return matched, breaks
    
    def _check_variances(self, trade_a: Trade, trade_b: Trade) -> list[BreakRecord]:
        """Deterministic variance detection for CDS."""
        variances = []
        
        # Notional check (within tolerance)
        notional_tolerance = abs(trade_a.notional * self.tolerance_bps / 10000)
        if abs(trade_a.notional - trade_b.notional) > notional_tolerance:
            var_pct = abs(trade_a.notional - trade_b.notional) / trade_a.notional * 100
            variances.append(BreakRecord(
                break_type="DATA_VARIANCE",
                trade_id=trade_a.internal_id,
                system_a=trade_a.system_source,
                system_b=trade_b.system_source,
                field_name="NOTIONAL",
                value_a=f"{trade_a.notional:,.0f}",
                value_b=f"{trade_b.notional:,.0f}",
                severity="HIGH" if var_pct > 1 else "MEDIUM",
                notes=f"Notional variance: {var_pct:.2f}%"
            ))
        
        # Coupon check (1bp tolerance)
        if trade_a.coupon and trade_b.coupon:
            coupon_diff_bps = abs(trade_a.coupon - trade_b.coupon) * 10000
            if coupon_diff_bps > 1:
                severity = "LOW" if coupon_diff_bps < 5 else "MEDIUM" if coupon_diff_bps < 25 else "HIGH"
                variances.append(BreakRecord(
                    break_type="DATA_VARIANCE",
                    trade_id=trade_a.internal_id,
                    system_a=trade_a.system_source,
                    system_b=trade_b.system_source,
                    field_name="COUPON",
                    value_a=f"{trade_a.coupon:.6f}",
                    value_b=f"{trade_b.coupon:.6f}",
                    severity=severity,
                    notes=f"Coupon variance: {coupon_diff_bps:.1f} bps"
                ))
        
        # Settlement date check (1 day tolerance)
        if trade_a.settlement_date and trade_b.settlement_date:
            date_diff = abs((trade_a.settlement_date - trade_b.settlement_date).days)
            if date_diff > 1:
                severity = "MEDIUM" if date_diff == 2 else "HIGH"
                variances.append(BreakRecord(
                    break_type="DATA_VARIANCE",
                    trade_id=trade_a.internal_id,
                    system_a=trade_a.system_source,
                    system_b=trade_b.system_source,
                    field_name="SETTLEMENT_DATE",
                    value_a=str(trade_a.settlement_date),
                    value_b=str(trade_b.settlement_date),
                    severity=severity,
                    notes=f"Settlement date variance: {date_diff} days"
                ))
        
        # Inception date check (should match exactly)
        if trade_a.effective_date != trade_b.effective_date:
            variances.append(BreakRecord(
                break_type="DATA_VARIANCE",
                trade_id=trade_a.internal_id,
                system_a=trade_a.system_source,
                system_b=trade_b.system_source,
                field_name="INCEPTION_DATE",
                value_a=str(trade_a.effective_date),
                value_b=str(trade_b.effective_date),
                severity="MEDIUM",
                notes="Inception date mismatch"
            ))
        
        # Reference entity check
        if trade_a.ref_entity and trade_b.ref_entity:
            if trade_a.ref_entity.upper() != trade_b.ref_entity.upper():
                variances.append(BreakRecord(
                    break_type="DATA_VARIANCE",
                    trade_id=trade_a.internal_id,
                    system_a=trade_a.system_source,
                    system_b=trade_b.system_source,
                    field_name="REF_ENTITY",
                    value_a=trade_a.ref_entity,
                    value_b=trade_b.ref_entity,
                    severity="HIGH",
                    notes="Reference entity mismatch"
                ))
        
        # Recovery assumption check (5% tolerance)
        if trade_a.recovery_assumption and trade_b.recovery_assumption:
            recovery_diff = abs(trade_a.recovery_assumption - trade_b.recovery_assumption)
            if recovery_diff > 0.05:
                severity = "LOW" if recovery_diff < 0.10 else "MEDIUM" if recovery_diff < 0.25 else "HIGH"
                variances.append(BreakRecord(
                    break_type="DATA_VARIANCE",
                    trade_id=trade_a.internal_id,
                    system_a=trade_a.system_source,
                    system_b=trade_b.system_source,
                    field_name="RECOVERY_ASSUMPTION",
                    value_a=f"{trade_a.recovery_assumption:.2%}",
                    value_b=f"{trade_b.recovery_assumption:.2%}",
                    severity=severity,
                    notes=f"Recovery assumption variance: {recovery_diff:.2%}"
                ))
        
        # Counterparty check
        if trade_a.counterparty.upper() != trade_b.counterparty.upper():
            variances.append(BreakRecord(
                break_type="DATA_VARIANCE",
                trade_id=trade_a.internal_id,
                system_a=trade_a.system_source,
                system_b=trade_b.system_source,
                field_name="COUNTERPARTY",
                value_a=trade_a.counterparty,
                value_b=trade_b.counterparty,
                severity="HIGH",
                notes="Counterparty name mismatch"
            ))
        
        return variances
