# Tenant registry — one file per teacher

Each `<slug>.json` is the single source of truth for a teacher's branded Acharya instance on the
shared Gurukul box. Created + maintained by the **`acharya-technology-transfer`** skill.

- `_TEMPLATE.json` — copy this to `<slug>.json` for a new teacher.
- `slug` = kebab-case, doubles as the `course_id` and the tenant key.
- Keep `status` current: `provisioning → live → paid | churned`.
- `brand.logo` + `brand.colors` are captured now and applied on the web in the multi-tenant
  fast-follow (skill §7); the tutor is branded by `name` immediately.

Do not put secrets here (no tokens/keys) — this file is for config + brand + roster only.
