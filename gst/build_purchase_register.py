#!/usr/bin/env python3
"""Build the monthly GST purchase register for TrigunAI.

Takes a hand-filled CSV of vendor invoices (one row per invoice, see
purchases_TEMPLATE.csv) and produces the register your CA files from:

  * imports of service  -> reverse charge (RCM), IGST self-paid then reclaimed
  * domestic invoices   -> normal input tax credit (ITC)

Classification is driven by the data, not by vendor name: a row with an Indian
supplier GSTIN is domestic ITC; a row without one, billed in foreign currency,
is an import of service under RCM.

Usage:
    python3 gst/build_purchase_register.py gst/purchases_2026-07.csv
    python3 gst/build_purchase_register.py gst/purchases_2026-07.csv --rate 18
"""

from __future__ import annotations

import argparse
import csv
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

TWO = Decimal("0.01")


def money(x: Decimal) -> Decimal:
    return x.quantize(TWO, rounding=ROUND_HALF_UP)


class RowError(Exception):
    pass


def parse_row(raw: dict, lineno: int) -> dict:
    def need(key: str) -> str:
        v = (raw.get(key) or "").strip()
        if not v:
            raise RowError(f"line {lineno}: missing required column '{key}'")
        return v

    currency = need("currency").upper()
    try:
        amount = Decimal(need("amount").replace(",", ""))
    except Exception:
        raise RowError(f"line {lineno}: amount '{raw.get('amount')}' is not a number")

    fx_raw = (raw.get("fx_rate") or "").strip().replace(",", "")
    if currency == "INR":
        fx = Decimal(1)
    else:
        if not fx_raw:
            raise RowError(
                f"line {lineno}: {currency} invoice needs an fx_rate "
                f"(exchange rate on the invoice date)"
            )
        fx = Decimal(fx_raw)
        if fx <= 0:
            raise RowError(f"line {lineno}: fx_rate must be positive")

    gstin = (raw.get("supplier_gstin") or "").strip().upper()
    gst_charged_raw = (raw.get("gst_charged") or "").strip().replace(",", "")
    gst_charged = Decimal(gst_charged_raw) if gst_charged_raw else Decimal(0)

    # An Indian supplier GSTIN means the vendor already charged GST -> normal ITC.
    # No GSTIN on a foreign-currency invoice means import of service -> RCM.
    domestic = bool(gstin)

    if domestic and gst_charged == 0:
        note = "WARNING: has GSTIN but gst_charged is 0 - confirm with CA"
    else:
        note = ""

    return {
        "date": need("invoice_date"),
        "vendor": need("vendor"),
        "invoice_no": (raw.get("invoice_no") or "").strip(),
        "description": (raw.get("description") or "").strip(),
        "currency": currency,
        "amount": amount,
        "fx": fx,
        "inr": money(amount * fx),
        "gstin": gstin,
        "gst_charged": money(gst_charged),
        "domestic": domestic,
        "warning": note,
        "notes": (raw.get("notes") or "").strip(),
    }


def build(path: Path, rcm_rate: Decimal) -> tuple[list[dict], list[dict]]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"{path}: no data rows")

    imports, domestic = [], []
    errors = []
    for i, raw in enumerate(rows, start=2):
        if not any((v or "").strip() for v in raw.values()):
            continue
        try:
            r = parse_row(raw, i)
        except RowError as e:
            errors.append(str(e))
            continue
        if r["domestic"]:
            # Vendor charged GST; taxable value is the amount net of that tax.
            r["taxable"] = money(r["inr"] - r["gst_charged"])
            r["itc"] = r["gst_charged"]
            domestic.append(r)
        else:
            # Import of service: we self-assess IGST on the full invoice value.
            r["taxable"] = r["inr"]
            r["igst_rcm"] = money(r["inr"] * rcm_rate / Decimal(100))
            imports.append(r)

    if errors:
        for e in errors:
            print(f"  ERROR  {e}", file=sys.stderr)
        raise SystemExit(f"\n{len(errors)} row(s) could not be parsed. Fix and re-run.")

    return imports, domestic


def render(imports: list[dict], domestic: list[dict], rcm_rate: Decimal) -> str:
    out: list[str] = []
    w = out.append

    w("=" * 78)
    w("GST PURCHASE REGISTER — TrigunAI Innovations")
    w("=" * 78)

    w("")
    w(f"A. IMPORT OF SERVICES — REVERSE CHARGE @ {rcm_rate}% IGST")
    w("-" * 78)
    if not imports:
        w("  (none)")
    total_imp = Decimal(0)
    total_igst = Decimal(0)
    for r in imports:
        w(f"  {r['date']}  {r['vendor'][:34]:<34} {r['currency']} {r['amount']:>10,.2f}")
        w(
            f"      inv {r['invoice_no'] or '-':<20} @ {r['fx']:>7,.2f} "
            f"= INR {r['inr']:>12,.2f}   IGST {r['igst_rcm']:>10,.2f}"
        )
        if r["description"]:
            w(f"      {r['description']}")
        total_imp += r["inr"]
        total_igst += r["igst_rcm"]
    w("-" * 78)
    w(f"  {'Taxable value (imports)':<48} INR {total_imp:>14,.2f}")
    w(f"  {'IGST payable under RCM':<48} INR {total_igst:>14,.2f}")
    w(f"  {'IGST reclaimable as ITC (same amount)':<48} INR {total_igst:>14,.2f}")

    w("")
    w("B. DOMESTIC PURCHASES — NORMAL INPUT TAX CREDIT")
    w("-" * 78)
    if not domestic:
        w("  (none)")
    total_dom = Decimal(0)
    total_itc = Decimal(0)
    for r in domestic:
        w(f"  {r['date']}  {r['vendor'][:34]:<34} INR {r['inr']:>10,.2f}")
        w(
            f"      inv {r['invoice_no'] or '-':<20} GSTIN {r['gstin']:<16} "
            f"ITC {r['itc']:>10,.2f}"
        )
        if r["warning"]:
            w(f"      !! {r['warning']}")
        total_dom += r["taxable"]
        total_itc += r["itc"]
    w("-" * 78)
    w(f"  {'Taxable value (domestic)':<48} INR {total_dom:>14,.2f}")
    w(f"  {'ITC available':<48} INR {total_itc:>14,.2f}")

    w("")
    w("C. SUMMARY FOR GSTR-3B")
    w("=" * 78)
    w(f"  3.1(d) Inward supplies liable to reverse charge   INR {total_imp:>14,.2f}")
    w(f"         IGST payable thereon                       INR {total_igst:>14,.2f}")
    w(f"  4(A)(3) ITC on reverse charge inward supplies     INR {total_igst:>14,.2f}")
    w(f"  4(A)(5) All other ITC                             INR {total_itc:>14,.2f}")
    w("")
    w(f"  Net cash impact of RCM this month                 INR {'0.00':>14}")
    w("         (IGST self-paid, then reclaimed in full — provided the spend")
    w("          is for taxable business use and it IS declared)")
    w("")
    w("  Total input credit available to offset output tax:")
    w(f"                                                     INR {total_igst + total_itc:>14,.2f}")
    w("=" * 78)
    w("")
    w("NOTES FOR THE CA")
    w("  * RCM rate assumed 18% — confirm per service category.")
    w("  * FX rate must be the rate applicable on the invoice date (Rule 34).")
    w("  * ITC on RCM is claimable only after the IGST is actually paid in cash.")
    w("  * Not prepared by a chartered accountant. Figures are assembled from")
    w("    vendor invoices for the CA's review, not filed advice.")

    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", type=Path, help="filled purchases CSV for the month")
    ap.add_argument(
        "--rate",
        type=Decimal,
        default=Decimal(18),
        help="RCM IGST rate percent (default 18)",
    )
    ap.add_argument("-o", "--out", type=Path, help="also write the register to a file")
    args = ap.parse_args()

    if not args.csv.exists():
        raise SystemExit(
            f"{args.csv} not found.\n"
            f"Copy gst/purchases_TEMPLATE.csv to {args.csv} and fill in the month's "
            f"invoices."
        )

    imports, domestic = build(args.csv, args.rate)
    report = render(imports, domestic, args.rate)
    print(report)

    if args.out:
        args.out.write_text(report + "\n", encoding="utf-8")
        print(f"\nWritten to {args.out}")


if __name__ == "__main__":
    main()
