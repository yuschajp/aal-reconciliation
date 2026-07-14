from aal_reconciliation.parsers.base import BaseParser
from aal_reconciliation.models import Trade
from datetime import datetime
import pandas as pd


class ImagineParser(BaseParser):
    """Parse Imagine TS CSV export into Trade objects."""
    
    def parse(self) -> list[Trade]:
        trades = []
        for _, row in self.df.iterrows():
            try:
                # Extract dates safely
                effective_date = None
                if pd.notna(row.get("EffectiveDate")):
                    effective_date = datetime.strptime(str(row["EffectiveDate"]), "%Y-%m-%d").date()
                
                settlement_date = None
                if pd.notna(row.get("SettlementDate")):
                    settlement_date = datetime.strptime(str(row["SettlementDate"]), "%Y-%m-%d").date()
                
                # Extract rates safely
                fixed_rate = None
                if pd.notna(row.get("FixedRate")):
                    fixed_rate = float(row["FixedRate"])
                
                coupon = None
                if pd.notna(row.get("Coupon")):
                    coupon = float(row["Coupon"])
                
                trade = Trade(
                    internal_id=str(row["RefID"]),
                    system_source="IMAGINE_TS",
                    counterparty=str(row["Counterparty"]),
                    asset_class=str(row.get("ProductType", "")).upper(),
                    effective_date=effective_date,
                    notional=float(row["Notional"]),
                    fixed_rate=fixed_rate,
                    float_index=row.get("FloatIndex"),
                    settlement_date=settlement_date,
                    coupon=coupon,
                    ref_entity=row.get("RefEntity"),
                    recovery_assumption=float(row["RecoveryAssumption"]) if pd.notna(row.get("RecoveryAssumption")) else None,
                    raw_row=row.to_dict()
                )
                trades.append(trade)
            except Exception as e:
                print(f"⚠ Skipping row in Imagine TS: {e}")
                continue
        
        return trades
