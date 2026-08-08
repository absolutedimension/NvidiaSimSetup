# TrigunAI — Sample Log (the training set)

> **This is the dataset.** Every row = one real market interaction where a human was **asked to pay**.
> The label is the outcome. A priced **NO + reason** is valid data; a **NOT-ASKED** is a dropped sample.
> Rule: no priced ask → no row → no learning. Target: **≥5 priced asks / week.** First goal: **one PAID.**
>
> Companion to `SYSTEMS_THINKING_PLAYBOOK.md §8–§9` (why), `trigunai-sales-rehearsal` (rehearse the ask +
> capture the objection), `trigunai-campaign-tracker` (auto-captures the online PAID label via pulse).
> Keep this a plain table — a markdown log, NOT a CRM. Automate only when volume forces it.

## How to use
1. Before an interaction: know the **offer + price** you'll ask for.
2. After it: add a row. Be honest — "interested" is **not** PAID; only money (or a signed paid commitment) is.
3. Always fill **WHY** — the reason is the highest-value part of the sample.
4. Vary ONE thing across rows (price / pitch / buyer) so the samples form clean arms.
5. Weekly: count priced asks + read the WHY column for the pattern. Change the *experiment*, not the product.

## Labels
- **PAID** — money cleared / signed paid commitment (the positive label)
- **NO** — asked, declined (negative label — REQUIRES a reason)
- **DEFER** — "maybe later" (weak signal; log the blocker)
- **NOT-ASKED** — interaction happened, no price requested (a *miss* — log it to see how often you skip the ask)

## The dataset

| Date | Buyer (type + name) | Channel | Offer | Price asked | Outcome | WHY (reason / objection) | Next step |
|------|--------------------|---------|-------|-------------|---------|--------------------------|-----------|
| YYYY-MM-DD | e.g. Institute — <name> | Rohan visit / Maya / WhatsApp / landing | e.g. 1-mo pilot, Class-12 batch | ₹4,999/mo | NOT-ASKED | (example row — replace) | book paid pilot |
|  |  |  |  |  |  |  |  |

## Weekly rollup (fill each Sunday)
```
Week of ____:  priced asks = __ / target 5    PAID = __    NO = __    DEFER = __    NOT-ASKED (misses) = __
Top objection this week: ____________________
This changed my next experiment to: ____________________   (change the experiment, not the product)
```
