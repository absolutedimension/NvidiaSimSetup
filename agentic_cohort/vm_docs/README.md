# TrigunAI Gurukul — Docs Index (on the VM)

These docs document the live AI-tutoring system on this box, for the admin (Sutradhaar) and future
sessions. Read any with `cat ~/.openclaw/docs/<file>`.

- **00_SYSTEM_OVERVIEW.md** — what the system is, architecture, end-to-end flow, key IDs, the two personas.
- **01_OPERATIONS.md** — file/service map, all the ops commands, how to add concepts / edit Acharya /
  broadcast / run SRS / edit the bridge. **Start here for "how do I change X".**
- **02_TROUBLESHOOTING.md** — gotchas & fixes (the 24h-window delivery rule, onboarding, why-not-WhatsApp-Web,
  fallback replies, GPT-5 Responses API, template errors). **Start here for "why doesn't X work".**
- **03_WHATSAPP_META.md** — Meta Cloud API config, webhook wiring, templates, and the **production-number
  migration** steps (+919135255107, pending business verification).

Quick health check:
```
systemctl --user status wa-bridge openclaw-gateway
curl -s localhost:8788/health
journalctl --user -u wa-bridge -n 20 --no-pager
```

Secrets live in `~/.openclaw/wa_cloud.env` — never print them.
Repo backup of these docs (on Deepak's Mac): `NvidiaSimSetup/agentic_cohort/vm_docs/`.
