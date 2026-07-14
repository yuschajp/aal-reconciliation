import argparse
import json
from pathlib import Path
from datetime import datetime
from aal_reconciliation.parsers import ImagineParser, NorthStarParser, SSCParser
from aal_reconciliation.matchers import SwapsMatcher, CDSMatcher
from aal_reconciliation.models import ReconciliationReport, BreakRecord


def main():
    parser = argparse.ArgumentParser(
        description="AAL Reconciliation Engine: Multi-system trade reconciliation for swaps and CDS."
    )
    parser.add_argument("--imagine", required=True, help="Path to Imagine TS CSV export")
    parser.add_argument("--northstar", required=True, help="Path to North Star CSV export")
    parser.add_argument("--ssc", required=True, help="Path to SS&C CSV export")
    parser.add_argument("--asset-class", required=True, choices=["SWAPS", "CDS"], help="Asset class to reconcile")
    parser.add_argument("--tolerance", type=float, default=5, help="Notional tolerance in basis points (default: 5)")
    parser.add_argument("--output", default="results", help="Output directory for reports (default: results)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Validate input files
    for filepath in [args.imagine, args.northstar, args.ssc]:
        if not Path(filepath).exists():
            print(f"✗ File not found: {filepath}")
            exit(1)
    
    # Parse CSVs
    print(f"✓ Parsing Imagine TS: {args.imagine}")
    imagine_trades = ImagineParser(args.imagine).parse()
    print(f"  → {len(imagine_trades)} trades loaded")
    
    print(f"✓ Parsing North Star: {args.northstar}")
    northstar_trades = NorthStarParser(args.northstar).parse()
    print(f"  → {len(northstar_trades)} trades loaded")
    
    print(f"✓ Parsing SS&C: {args.ssc}")
    ssc_trades = SSCParser(args.ssc).parse()
    print(f"  → {len(ssc_trades)} trades loaded")
    
    # Initialize matcher
    if args.asset_class == "SWAPS":
        matcher = SwapsMatcher(tolerance_bps=args.tolerance)
    else:  # CDS
        matcher = CDSMatcher(tolerance_bps=args.tolerance)
    
    # Match Imagine vs North Star
    print(f"\n✓ Reconciling {args.asset_class} trades (Imagine TS vs North Star)...")
    matched_ab, breaks_ab = matcher.match_trades(imagine_trades, northstar_trades)
    
    # Match result vs SS&C
    print(f"✓ Reconciling {args.asset_class} trades (Result vs SS&C)...")
    imagine_matched = [t[0] for t in matched_ab]
    matched_abc, breaks_c = matcher.match_trades(imagine_matched, ssc_trades)
    
    all_breaks = breaks_ab + breaks_c
    
    # Summary
    unmatched_count = len([b for b in all_breaks if "UNMATCHED" in b.break_type])
    variance_count = len([b for b in all_breaks if "VARIANCE" in b.break_type])
    
    print(f"\n{'━' * 50}")
    print(f"Reconciliation Summary ({args.asset_class})")
    print(f"{'━' * 50}")
    print(f"Imagine TS:      {len(imagine_trades):,} trades")
    print(f"North Star:      {len(northstar_trades):,} trades")
    print(f"SS&C:            {len(ssc_trades):,} trades")
    print(f"")
    print(f"✓ Matched:       {len(matched_abc):,}")
    print(f"⚠ Unmatched:     {unmatched_count}")
    print(f"⚠ Variances:     {variance_count}")
    print(f"")
    
    if all_breaks:
        severity_counts = {}
        for b in all_breaks:
            severity = b.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            if severity in severity_counts:
                print(f"  {severity:8s}: {severity_counts[severity]}")
    
    # Write output
    Path(args.output).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(args.output) / f"recon_{args.asset_class.lower()}_{timestamp}.json"
    
    report = ReconciliationReport(
        reconciliation_date=datetime.now().isoformat(),
        asset_class=args.asset_class,
        summary={
            "imagine_count": len(imagine_trades),
            "northstar_count": len(northstar_trades),
            "ssc_count": len(ssc_trades),
            "matched": len(matched_abc),
            "unmatched": unmatched_count,
            "variances": variance_count,
            "tolerance_bps": args.tolerance,
        },
        breaks=all_breaks
    )
    
    with open(output_file, "w") as f:
        json.dump(report.dict(), f, indent=2, default=str)
    
    print(f"\n→ Report saved: {output_file}")
    
    if args.verbose and all_breaks:
        print(f"\n{'━' * 50}")
        print("Breaks Detail")
        print(f"{'━' * 50}")
        for i, brk in enumerate(all_breaks[:10], 1):  # Show first 10
            print(f"\n{i}. {brk.break_type} - {brk.trade_id}")
            print(f"   Severity: {brk.severity}")
            print(f"   {brk.notes}")
            if brk.field_name:
                print(f"   Field: {brk.field_name} | {brk.value_a} vs {brk.value_b}")
        
        if len(all_breaks) > 10:
            print(f"\n... and {len(all_breaks) - 10} more breaks (see full report for details)")


if __name__ == "__main__":
    main()
