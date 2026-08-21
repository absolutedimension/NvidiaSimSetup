# TrigunAI — GST Vendor Register

Every vendor this codebase actually touches, derived from the repo (imports, config,
docs, deploy scripts). Purpose: **so no vendor is missed** when collecting invoices
for the monthly GST filing.

> ⚠️ This file is a **checklist of where to download invoices from** — it is NOT a
> substitute for the invoices. The repo contains only rough engineering cost
> estimates (`CLAUDE.md` §9: "~$7 session", "~$16/mo EBS"). Those are guesses made
> while building, not tax documents. Every number below must come from a real
> downloaded invoice.

---

## The one rule that decides RCM vs normal ITC

Do **not** classify by brand name. Classify by **what the invoice header says**:

| What the invoice shows | Treatment |
|---|---|
| An **Indian GSTIN** on the supplier, GST charged as a line item, amount in ₹ | **Normal ITC.** Vendor already paid the GST. You just claim credit. |
| **No Indian GSTIN**, foreign entity, amount in USD/EUR | **Reverse charge (RCM).** You self-pay IGST, then claim it back as ITC. |

Same brand can be either. AWS, Azure, and Google all have Indian billing entities
*and* foreign ones — which one bills you depends on how your account was set up.
**Open one invoice from each and look at the header.** Do this once; it won't change.

Also check: your own **GSTIN must be on file** with each vendor. If it isn't, the
invoice comes without it and your CA cannot claim the credit. Every one of these
consoles has a "tax settings / GSTIN" field. Fill it in — this is free money you
are currently leaving behind.

---

## Compute & AI — the big ones

| Vendor | What we use it for | Where to download the invoice | Likely treatment |
|---|---|---|---|
| **Amazon Web Services** | EC2 g5.2xlarge `i-047ebf759f2386e71` (us-east-1) + `i-05d9104a0d7bf56be` (ap-south-1 Mumbai), 200 GiB EBS, S3 | Billing Console → **Bills** → *Invoices* tab → download PDF per month | Check header: AWS Inc (USD) = **RCM**; AISPL / AWS India (₹, GSTIN) = **normal ITC** |
| **Microsoft Azure** | OpenAI models (`azure-trigunai-model` eastus, `deepa-mmq3sitb` eastus2), Container Apps (lms, lms-kids, gurukul), Postgres, T4 + PMC VMs, Speech | Azure Portal → **Cost Management + Billing** → *Invoices* → download | Check header. Often Microsoft Regional Sales Pte (Singapore) = **RCM** |
| **Anthropic (Claude)** | Claude API + Claude Code | console.anthropic.com → **Settings → Billing** → invoice history | US entity, USD → **RCM** |
| **OpenAI (direct)** | ⚠️ Verify — repo uses the `openai` SDK but points it at **Azure**. If there is no direct platform.openai.com spend, this row is nil. | platform.openai.com → Settings → Billing | USD → **RCM** if any |
| **Hugging Face** | Datasets for the question bank | huggingface.co → Billing | Free tier likely → nil. **RCM** if Pro/Inference |

## Marketing & distribution

| Vendor | Use | Where | Treatment |
|---|---|---|---|
| **Google Ads** | Campaigns (`marketing_pipeline/google_ads/`) | Google Ads → Billing → **Documents** | Google India Pvt Ltd, ₹ + GSTIN → **normal ITC** |
| **Meta (Facebook/Instagram)** | Reels publishing via Graph API | business.facebook.com → Billing | Organic posting = free. Paid ads: Meta India → **normal ITC** |
| **YouTube Data API** | Uploads to both channels | — | Free quota → nil |

## Infrastructure & services

| Vendor | Use | Where | Treatment |
|---|---|---|---|
| **Razorpay** | Payment gateway (`lms/app/billing.py`) | Dashboard → Account & Settings → **GST invoices** | Indian, GST charged on fees → **normal ITC**. Easy to forget — the fee is deducted at source so you never "pay a bill". Download it anyway. |
| **Twilio** | Maya voice calling (`maya_twilio.py`) | console.twilio.com → Billing | USD → **RCM** |
| **Cloudflare** | Quick tunnels for WebXR | dash.cloudflare.com → Billing | Free quick-tunnel → nil. **RCM** if on a paid plan |
| **GitHub** | Repos / Copilot | github.com → Settings → Billing | Free → nil. **RCM** if paid |
| **ElevenLabs** | Voice (1 reference in repo — verify if live) | elevenlabs.io → Billing | USD → **RCM** if used |
| **Stripe** | ⚠️ 11 references — verify whether actually live or vestigial | dashboard.stripe.com | Check entity |
| **Domain + DNS** (trigunai.com) | Registrar not found in repo — check your card statement | registrar console | Depends on registrar |

## Not in the repo — check anyway

These never appear in code but are real business expenses with claimable GST:

- Apple / MacBook, monitors, any hardware purchase
- CA fees, ROC filing fees, company secretary
- Internet / broadband (if in company name)
- Co-working or office rent
- Meta Quest 3, reSpeaker, any dev hardware

---

## Monthly collection routine

1. Download the month's invoice PDF from: **AWS, Azure, Anthropic, Razorpay, Google Ads** (the five that always have something)
2. Drop them all in `gst/invoices/YYYY-MM/`
3. Fill one row per invoice in `gst/purchases_YYYY-MM.csv` (template: `gst/purchases_TEMPLATE.csv`)
4. Run `python3 gst/build_purchase_register.py gst/purchases_YYYY-MM.csv`
5. Send your CA: the generated register + the PDF folder + the month's export invoice + the FIRC

---

## Why this matters even with almost no revenue

Reverse charge is a liability that **exists whether or not you earned anything**.
On foreign AI/cloud spend it is 18% — and at your burn rate that is not small.

The saving grace: when the spend is for taxable business use, the IGST you self-pay
comes straight back as input credit, so it **nets to roughly zero if declared**.
Undeclared, it becomes a demand with interest and penalty years later, and by then
the credit window to offset it has usually closed.

Declaring it costs you nothing. Not declaring it is the expensive option.
