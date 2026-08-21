#!/usr/bin/env python3
"""Generate a GST-compliant EXPORT OF SERVICES invoice for TrigunAI.

Export of services is zero-rated: no GST is charged to the client, but the
invoice must still carry the LUT endorsement, the SAC code, the place of supply,
and an INR equivalent for reporting in GSTR-1 Table 6A.

Outputs print-ready HTML (open it, Cmd+P, Save as PDF) and appends a row to the
sales register your CA files from.

Usage:
    python3 gst/make_export_invoice.py --date 2026-08-31 --fx 87.20
    python3 gst/make_export_invoice.py --date 2026-08-31 --fx 87.20 --amount 250
    python3 gst/make_export_invoice.py --date 2026-08-31 --fx 87.20 --period "August 2026"
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "company.json"
REGISTER = HERE / "sales_register.csv"
OUTDIR = HERE / "invoices"

TWO = Decimal("0.01")

REGISTER_COLUMNS = [
    "invoice_no", "invoice_date", "client", "country", "sac",
    "currency", "amount_fc", "fx_rate", "taxable_value_inr",
    "gst_rate", "igst", "supply_type", "lut_arn",
]


def money(x: Decimal) -> Decimal:
    return x.quantize(TWO, rounding=ROUND_HALF_UP)


def load_config() -> dict:
    if not CONFIG.exists():
        raise SystemExit(f"{CONFIG} not found.")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    unfilled: list[str] = []

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("_"):
                    continue
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and "FILL_ME" in node:
            unfilled.append(path)

    walk(cfg)
    if unfilled:
        print("Cannot generate — these fields in gst/company.json are still", file=sys.stderr)
        print("placeholders:\n", file=sys.stderr)
        for u in unfilled:
            print(f"    {u}", file=sys.stderr)
        raise SystemExit(
            "\nFill them and re-run. The GSTIN, LUT ARN and client address are "
            "mandatory on an export invoice — an invoice without them is not valid."
        )
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def amount_in_words(rupees: Decimal) -> str:
    """Indian numbering system, for the mandatory amount-in-words line."""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
            "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
            "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy",
            "Eighty", "Ninety"]

    def under_100(n: int) -> str:
        if n < 20:
            return ones[n]
        return (tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")).strip()

    def under_1000(n: int) -> str:
        if n < 100:
            return under_100(n)
        head = ones[n // 100] + " Hundred"
        return (head + (" " + under_100(n % 100) if n % 100 else "")).strip()

    whole = int(rupees)
    paise = int((rupees - whole) * 100)

    if whole == 0:
        words = "Zero"
    else:
        parts: list[str] = []
        for divisor, label in ((10_000_000, "Crore"), (100_000, "Lakh"), (1_000, "Thousand")):
            if whole >= divisor:
                parts.append(f"{under_1000(whole // divisor)} {label}")
                whole %= divisor
        if whole:
            parts.append(under_1000(whole))
        words = " ".join(parts)

    out = f"Indian Rupees {words}"
    if paise:
        out += f" and {under_100(paise)} Paise"
    return out + " Only"


def next_invoice_number(cfg: dict) -> tuple[str, int]:
    inv = cfg["invoice"]
    n = int(inv["next_number"])
    return f"{inv['series_prefix']}{n:03d}", n


def already_issued(invoice_no: str) -> bool:
    if not REGISTER.exists():
        return False
    with REGISTER.open(newline="", encoding="utf-8") as fh:
        return any(r.get("invoice_no") == invoice_no for r in csv.DictReader(fh))


def append_register(row: dict) -> None:
    new = not REGISTER.exists()
    with REGISTER.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=REGISTER_COLUMNS)
        if new:
            w.writeheader()
        w.writerow(row)


def render_html(cfg: dict, ctx: dict) -> str:
    s, c, lut, svc, bank = (
        cfg["supplier"], cfg["client"], cfg["lut"], cfg["service"], cfg["bank"]
    )
    e = html.escape

    def lines(xs: list[str]) -> str:
        return "<br>".join(e(x) for x in xs)

    return f"""<!doctype html>
<meta charset="utf-8">
<title>{e(ctx['invoice_no'])}</title>
<style>
  @page {{ size: A4; margin: 14mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font: 11pt/1.5 -apple-system, "Helvetica Neue", Arial, sans-serif;
         color: #111; margin: 0; }}
  .doc {{ max-width: 190mm; margin: 0 auto; }}
  h1 {{ font-size: 15pt; letter-spacing: .16em; margin: 0 0 2px;
        text-transform: uppercase; }}
  .sub {{ font-size: 9pt; color: #666; letter-spacing: .08em;
          text-transform: uppercase; }}
  .rule {{ border: 0; border-top: 2px solid #111; margin: 12px 0 16px; }}
  .row {{ display: flex; gap: 24px; }}
  .col {{ flex: 1; }}
  .lbl {{ font-size: 8pt; color: #777; letter-spacing: .1em;
          text-transform: uppercase; margin-bottom: 3px; }}
  .name {{ font-weight: 700; }}
  table {{ width: 100%; border-collapse: collapse; margin: 18px 0 0; }}
  th {{ text-align: left; font-size: 8pt; letter-spacing: .1em; color: #777;
        text-transform: uppercase; border-bottom: 1.5px solid #111;
        padding: 0 0 6px; }}
  td {{ padding: 10px 0; border-bottom: 1px solid #e0e0e0;
        vertical-align: top; }}
  .r {{ text-align: right; }}
  .totals {{ margin-left: auto; width: 62%; margin-top: 14px; }}
  .totals td {{ border: 0; padding: 4px 0; }}
  .grand td {{ border-top: 2px solid #111; padding-top: 9px;
               font-weight: 700; font-size: 12.5pt; }}
  .zero {{ color: #666; }}
  .endorse {{ border: 1.5px solid #111; padding: 11px 13px; margin: 20px 0;
              font-size: 9.5pt; }}
  .endorse b {{ display: block; text-transform: uppercase; letter-spacing: .04em;
                margin-bottom: 4px; }}
  .words {{ font-size: 9.5pt; margin-top: 12px; }}
  .foot {{ margin-top: 26px; display: flex; gap: 24px; font-size: 9pt; }}
  .sig {{ margin-left: auto; text-align: right; min-width: 62mm; }}
  .sigline {{ margin-top: 34px; border-top: 1px solid #111; padding-top: 5px; }}
  .muted {{ color: #666; }}
  @media print {{ .noprint {{ display: none; }} }}
  .noprint {{ background: #fffbe6; border: 1px solid #e6d795; padding: 9px 12px;
              font-size: 9.5pt; margin-bottom: 16px; border-radius: 4px; }}
</style>
<div class="doc">

<div class="noprint">Press <b>Cmd&nbsp;+&nbsp;P</b> → <b>Save as PDF</b>. This banner will not print.</div>

<h1>Tax Invoice</h1>
<div class="sub">Export of Services &middot; Zero-Rated Supply</div>
<hr class="rule">

<div class="row">
  <div class="col">
    <div class="lbl">Supplier</div>
    <div class="name">{e(s['legal_name'])}</div>
    <div>{lines(s['address_lines'])}</div>
    <div style="margin-top:7px">
      GSTIN <b>{e(s['gstin'])}</b><br>
      PAN {e(s['pan'])}{f"<br>CIN {e(s['cin'])}" if s.get('cin') else ""}<br>
      {e(s['email'])} &middot; {e(s['phone'])}
    </div>
  </div>
  <div class="col">
    <div class="lbl">Bill To (Recipient)</div>
    <div class="name">{e(c['legal_name'])}</div>
    <div>{lines(c['address_lines'])}</div>
    <div style="margin-top:7px">{e(c['country'])}</div>
    <div class="muted" style="margin-top:7px">
      GSTIN: Not applicable — recipient outside India
    </div>
  </div>
  <div class="col">
    <div class="lbl">Invoice</div>
    <div class="name">{e(ctx['invoice_no'])}</div>
    <div style="margin-top:7px">
      Date <b>{e(ctx['date_disp'])}</b><br>
      Place of supply: <b>Outside India</b><br>
      Country: {e(c['country'])}<br>
      Currency: {e(ctx['currency'])}
    </div>
  </div>
</div>

<table>
  <thead>
    <tr>
      <th style="width:50%">Description of Service</th>
      <th style="width:12%">SAC</th>
      <th class="r" style="width:12%">Rate</th>
      <th class="r" style="width:12%">GST</th>
      <th class="r" style="width:14%">Amount</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <b>{e(svc['description'])}</b>
        {f"<br><span class='muted'>Service period: {e(ctx['period'])}</span>" if ctx.get('period') else ""}
      </td>
      <td>{e(svc['sac_code'])}</td>
      <td class="r">0%</td>
      <td class="r zero">Nil</td>
      <td class="r">{e(ctx['currency'])} {ctx['amount']:,.2f}</td>
    </tr>
  </tbody>
</table>

<table class="totals">
  <tr>
    <td>Taxable value</td>
    <td class="r">{e(ctx['currency'])} {ctx['amount']:,.2f}</td>
  </tr>
  <tr class="zero">
    <td>IGST @ 0% (zero-rated export under LUT)</td>
    <td class="r">Nil</td>
  </tr>
  <tr class="grand">
    <td>Total payable</td>
    <td class="r">{e(ctx['currency'])} {ctx['amount']:,.2f}</td>
  </tr>
  <tr>
    <td class="muted" style="padding-top:9px">
      INR equivalent @ {ctx['fx']:,.4f} <span class="muted">(for GST reporting only)</span>
    </td>
    <td class="r muted" style="padding-top:9px">INR {ctx['inr']:,.2f}</td>
  </tr>
</table>

<div class="words">
  <span class="lbl" style="display:inline">Amount in words</span><br>
  {e(ctx['words'])} <span class="muted">(INR equivalent)</span>
</div>

<div class="endorse">
  <b>Supply meant for export of services under Letter of Undertaking
  without payment of Integrated Tax</b>
  LUT ARN: <b>{e(lut['arn'])}</b> &nbsp;&middot;&nbsp; Financial Year {e(lut['financial_year'])}<br>
  Declared under Rule 96A of the CGST Rules, 2017.
</div>

<div class="row" style="font-size:9pt">
  <div class="col">
    <div class="lbl">Remittance Details</div>
    {e(bank['account_name'])}<br>
    {e(bank['bank_name'])}<br>
    A/c {e(bank['account_number'])}<br>
    SWIFT {e(bank['swift'])} &middot; IFSC {e(bank['ifsc'])}<br>
    AD Code {e(bank['ad_code'])}
  </div>
  <div class="col">
    <div class="lbl">Declaration</div>
    <span class="muted">Payment to be received in convertible foreign
    exchange. This is a computer-generated invoice.</span>
  </div>
</div>

<div class="foot">
  <div class="sig">
    For <b>{e(s['legal_name'])}</b>
    <div class="sigline">Authorised Signatory</div>
  </div>
</div>

</div>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", required=True, help="invoice date, YYYY-MM-DD")
    ap.add_argument("--fx", required=True, type=Decimal,
                    help="INR per unit foreign currency on the invoice date")
    ap.add_argument("--amount", type=Decimal, help="override the default amount")
    ap.add_argument("--period", help='service period, e.g. "August 2026"')
    ap.add_argument("--number", type=int, help="force a specific invoice number")
    args = ap.parse_args()

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        raise SystemExit("--date must be YYYY-MM-DD")
    try:
        d: date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"--date invalid: {exc}")

    if args.fx <= 0:
        raise SystemExit("--fx must be positive")

    cfg = load_config()

    if args.number is not None:
        cfg["invoice"]["next_number"] = args.number
    invoice_no, number = next_invoice_number(cfg)

    if already_issued(invoice_no):
        raise SystemExit(
            f"{invoice_no} is already in {REGISTER.name}.\n"
            f"Invoice numbers must be unique and unbroken — re-issuing one breaks "
            f"the series. Use --number to pick the correct next one."
        )

    amount = args.amount if args.amount is not None else Decimal(cfg["invoice"]["default_amount"])
    if amount <= 0:
        raise SystemExit("--amount must be positive")
    amount = money(amount)
    inr = money(amount * args.fx)

    ctx = {
        "invoice_no": invoice_no,
        "date_disp": d.strftime("%d %B %Y"),
        "currency": cfg["invoice"]["currency"],
        "amount": amount,
        "fx": args.fx,
        "inr": inr,
        "words": amount_in_words(inr),
        "period": args.period or "",
    }

    OUTDIR.mkdir(exist_ok=True)
    safe = invoice_no.replace("/", "-")
    out = OUTDIR / f"{safe}.html"
    out.write_text(render_html(cfg, ctx), encoding="utf-8")

    append_register({
        "invoice_no": invoice_no,
        "invoice_date": args.date,
        "client": cfg["client"]["legal_name"],
        "country": cfg["client"]["country"],
        "sac": cfg["service"]["sac_code"],
        "currency": ctx["currency"],
        "amount_fc": f"{amount:.2f}",
        "fx_rate": f"{args.fx:.4f}",
        "taxable_value_inr": f"{inr:.2f}",
        "gst_rate": "0",
        "igst": "0.00",
        "supply_type": "Export of services under LUT (zero-rated)",
        "lut_arn": cfg["lut"]["arn"],
    })

    cfg["invoice"]["next_number"] = number + 1
    save_config(cfg)

    print(f"Invoice   {invoice_no}")
    print(f"Amount    {ctx['currency']} {amount:,.2f}  =  INR {inr:,.2f}  @ {args.fx}")
    print(f"HTML      {out}")
    print(f"Register  {REGISTER}  (row appended)")
    print(f"\nNext invoice will be number {number + 1:03d}.")
    print("\nOpen the HTML, Cmd+P, Save as PDF. Send that to the client;")
    print("send the PDF + the register + the FIRC to your CA.")


if __name__ == "__main__":
    main()
