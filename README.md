# AAL Reconciliation Engine

Multi-system trade reconciliation for capital markets. Matches swaps and CDS trades across Imagine TS, North Star, and SS&C, automatically detecting mismatches and data variances.

**Status:** MVP - Swaps + CDS reconciliation (CLI)

---

## Setup

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repo
git clone https://github.com/yuschajp/aal-reconciliation.git
cd aal-reconciliation

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Basic Command

```bash
python -m aal_reconciliation \
  --imagine data/imagine_export.csv \
  --northstar data/northstar_export.csv \
  --ssc data/ssc_export.csv \
  --asset-class SWAPS
```

### Options

- `--imagine` (required): Path to Imagine TS CSV export
- `--northstar` (required): Path to North Star CSV export
- `--ssc` (required): Path to SS&C CSV export
- `--asset-class` (required): `SWAPS` or `CDS`
- `--tolerance` (optional, default 5): Notional tolerance in basis points
- `--output` (optional, default `results`): Output directory for reports
- `--verbose` (optional): Show detailed break information

### Example Output

```
✓ Parsing Imagine TS: data/imagine_export.csv
  → 1,250 trades loaded
✓ Parsing North Star: data/northstar_export.csv
  → 1,248 trades loaded
✓ Parsing SS&C: data/ssc_export.csv
  → 1,250 trades loaded

✓ Reconciling SWAPS trades (Imagine TS vs North Star)...
✓ Reconciling SWAPS trades (Result vs SS&C)...

══════════════════════════════════════════════════════
Reconciliation Summary (SWAPS)
══════════════════════════════════════════════════════
Imagine TS:      1,250 trades
North Star:      1,248 trades
SS&C:            1,250 trades

✓ Matched:       1,247
⚠ Unmatched:     3
⚠ Variances:     12

  CRITICAL: 0
  HIGH    : 2
  MEDIUM  : 7
  LOW     : 3

→ Report saved: results/recon_swaps_20260721_093015.json
```

---

## CSV Format Requirements

All three system exports must contain the following columns (case-sensitive):

### Required (All Asset Classes)
- `RefID`: Internal reference ID (common across systems)
- `Counterparty`: Counterparty name
- `ProductType`: Asset class (`SWAPS`, `CDS`, etc.)
- `EffectiveDate`: Trade effective date (YYYY-MM-DD)
- `Notional`: Trade notional (numeric)

### Swaps-Specific
- `FixedRate`: Fixed leg rate (numeric, e.g., 0.035)
- `FloatIndex`: Floating index (string, e.g., "SOFR")
- `SettlementDate`: Settlement date (YYYY-MM-DD)

### CDS-Specific
- `Coupon`: CDS coupon (numeric, e.g., 0.01)
- `RefEntity`: Reference entity name
- `RecoveryAssumption`: Recovery % (numeric, e.g., 0.40)

---

## Output Format

Reconciliation reports are JSON with the following structure:

```json
{
  "reconciliation_date": "2026-07-21T09:30:15.123456",
  "asset_class": "SWAPS",
  "summary": {
    "imagine_count": 1250,
    "northstar_count": 1248,
    "ssc_count": 1250,
    "matched": 1247,
    "unmatched": 3,
    "variances": 12,
    "tolerance_bps": 5
  },
  "breaks": [
    {
      "break_type": "UNMATCHED_SYSTEM_A",
      "trade_id": "XX-2026-0051234",
      "system_a": "IMAGINE_TS",
      "severity": "HIGH",
      "notes": "Trade XX-2026-0051234 (JPM, 50,000,000) in IMAGINE_TS not found in comparison system."
    },
    {
      "break_type": "DATA_VARIANCE",
      "trade_id": "XX-2026-0051230",
      "system_a": "IMAGINE_TS",
      "system_b": "NORTHSTAR",
      "field_name": "FIXED_RATE",
      "value_a": "0.035000",
      "value_b": "0.034900",
      "severity": "LOW",
      "notes": "Fixed rate variance: 10.0 bps"
    }
  ]
}
```

### Break Types

- **UNMATCHED_SYSTEM_A**: Trade exists in first system but not others
- **UNMATCHED_SYSTEM_B**: Trade exists in comparison system but not first system
- **DATA_VARIANCE**: Trade matched but field values differ

### Severity Levels

- **CRITICAL**: Data integrity issue requiring immediate attention
- **HIGH**: Significant variance (>1% notional, >50bps rates)
- **MEDIUM**: Moderate variance (settlement date off by 2 days, etc.)
- **LOW**: Minor variance (<50bps rates, within tolerance)
- **INFO**: Informational (expected CSA daily var, etc.)

---

## Architecture

```
aal_reconciliation/
├── models.py           # Pydantic Trade, BreakRecord schemas
├── parsers/            # CSV parsers for each system
│   ├── imagine_ts.py
│   ├── northstar.py
│   └── ssc.py
├── matchers/           # Asset-class-specific reconciliation logic
│   ├── swaps.py
│   └── cds.py
└── __main__.py         # CLI entry point
```

### Key Design Principles

1. **No LLM arithmetic**: All notional, rate, and dollar math is deterministic Python
2. **Pydantic schemas**: Trade and BreakRecord are validated at parse time
3. **Asset-class isolation**: SwapsMatcher and CDSMatcher contain asset-specific variance logic
4. **Tolerance configuration**: Notional/rate thresholds passed at initialization

---

## Testing

Run unit tests with pytest:

```bash
pip install pytest
pytest tests/ -v
```

Test coverage includes:
- Exact match detection (no breaks)
- Notional variance detection and severity assignment
- Fixed rate / coupon variance thresholds
- Settlement date variance
- Unmatched trade detection

---

## Future Roadmap

- **Phase 2**: API integrations (live data vs CSV exports)
- **Phase 3**: Add Futures, PBs, Corporate Actions
- **Phase 4**: Web dashboard for break visualization + triage workflow
- **Phase 5**: Machine learning for anomaly detection

---

## Configuration for Saba Capital

This engine is configured for Saba Capital's reconciliation workflow:
- Daily swaps and CDS reconciliation
- Automatic break detection and escalation
- Integration with Imagine TS, North Star, and SS&C exports

**Contact:** Joe Yuschak (joe@saba.com)

---

## License

Proprietary - AI Alpha Labs
