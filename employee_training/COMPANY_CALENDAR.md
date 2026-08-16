# TrigunAI — Company Calendar & Saathi's Holiday Behaviour

> Saathi reads this so it **never sends a work-planning message on a day off**. On Sundays and company
> holidays, instead of the morning "aaj ka plan?", Rohan (or any employee) gets a **warm holiday
> greeting** — companion, not manager. Machine-readable version: `holidays_2026.json`.

---

## 1. Weekly off

- **Sunday = weekly off** for everyone. No morning planning ping, no evening close.
- **Saturday = working day** (field sales — institutes are open on Saturdays). *If you'd rather make
  Saturday off too, say so and I'll flip it.*

## 2. Saathi's behaviour on a day off

| Day type | Morning | Evening |
|---|---|---|
| **Working day** | Planning kickoff (asks the plan) | Evening close (how'd it go) |
| **Sunday** | Warm greeting only — *"Happy Sunday, Rohan! 🌿 Aaj aaram karo, family ke saath time bitao. Kal milte hain 😊"* | (nothing) |
| **Company holiday** | Festival greeting — *"Happy Diwali, Rohan! 🪔 Aaj ka din apno ke saath enjoy karo. Kaam kal se 😊"* | (nothing) |

- No plan is asked, nothing is "due," and a missed day off **never** counts as a miss on the Mentor Cockpit.
- If Rohan messages Saathi *on* a holiday (his choice), it replies warmly and helps — it just won't push work.
- Optional: the **evening before** a holiday, Saathi can add "Kal chhutti hai — enjoy! 🎉" to the close.

## 3. TrigunAI Holiday List 2026

> ⚠️ **Please confirm/lock these dates.** The **fixed** national holidays are exact; the **festival**
> dates move by the lunar calendar every year — I've put best-effort 2026 dates, but **verify each
> festival against the official 2026 calendar** before we lock it (I don't want Saathi wishing "Happy
> Holi" on the wrong day). Being Patna-based, the list includes Bihar favourites (esp. **Chhath**).

### Fixed (exact)
| Date | Day | Holiday |
|---|---|---|
| 26 Jan 2026 | Mon | Republic Day |
| 15 Aug 2026 | Sat | Independence Day |
| 02 Oct 2026 | Fri | Gandhi Jayanti |
| 25 Dec 2026 | Fri | Christmas |

### Festivals (⚠️ confirm exact 2026 dates before locking)
| Approx. 2026 date | Holiday | Note |
|---|---|---|
| ~03 Mar | Holi | |
| ~26 Mar | Ram Navami | |
| ~03 Apr | Good Friday | |
| ~14 Apr | Ambedkar Jayanti / Vaisakhi | |
| ~21 Mar | Eid-ul-Fitr | lunar — confirm |
| ~27 May | Eid-ul-Adha (Bakrid) | lunar — confirm |
| ~26 Jun | Muharram | lunar — confirm |
| ~28 Aug | Raksha Bandhan | |
| ~04 Sep | Janmashtami | |
| ~20 Oct | Dussehra (Vijayadashami) | |
| ~08 Nov | Diwali | |
| ~09 Nov | Govardhan / Bhai Dooj | |
| **~15–16 Nov** | **Chhath Puja (2 days)** | **big in Bihar — likely a 2-day break** |
| ~24 Nov | Guru Nanak Jayanti | |

*Typical Indian company keeps ~10–14 gazetted holidays/year. Trim this to your final list — you may not
take every one. Just tell me which to keep and the exact dates, and I'll lock `holidays_2026.json`.*

## 4. How it works technically (build note)

- Saathi's morning/evening crons **check `holidays_2026.json` + day-of-week first.**
- Sunday or a listed holiday → send the greeting variant (or nothing in the evening), skip planning.
- The Mentor Cockpit treats days-off as **grey (not a miss)** — the streak/adherence ignore them.
- Editable in one place: update `holidays_2026.json` each year (or when the org adds a day).

See `DAILY_COMPANION.md` (§ Holidays) and `FEEDBACK_SYSTEM.md` (misses ignore days off).
