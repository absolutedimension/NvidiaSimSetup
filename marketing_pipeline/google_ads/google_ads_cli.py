#!/usr/bin/env python3
"""
TrigunAI Google Ads pipeline — one CLI to launch/manage Search campaigns from a YAML spec.

Reusable: a new campaign = a new file in campaigns/*.yaml. The spec holds ALL the marketing
(keywords, negatives, ad copy, geo, budget, bidding); this tool turns it into a live (paused)
campaign via the Google Ads API, and reports on it.

Commands
  check                         verify credentials + list accessible ad accounts
  dry-run  <spec.yaml>          validate the spec (char limits, fields) — NO API call, needs no creds
  launch   <spec.yaml> --customer <id>    create budget→campaign(PAUSED)→ad group→keywords→negatives→geo/lang→RSA
  report   --customer <id> [--days 14]    impressions / clicks / cost / CTR / avg CPC per campaign
  pause    --customer <id> --campaign <id>
  enable   --customer <id> --campaign <id>

Credentials: a google-ads.yaml (see google-ads.yaml.example + SETUP_CREDENTIALS.md).
  Pass --config PATH, or set GOOGLE_ADS_CONFIGURATION_FILE_PATH, or keep it beside this script.

Safety: launch ALWAYS creates the campaign PAUSED. Nothing spends until you enable it in the UI
or via `enable`. dry-run touches no account and needs no credentials.
"""
import argparse, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
INR_MICROS = 1_000_000          # Google Ads money is in "micros" of the account currency
H_MAX, D_MAX = 30, 90           # RSA headline / description character limits


# ---------- spec loading + validation (no Google dependency) ----------
def load_spec(path):
    import yaml
    with open(path) as f:
        spec = yaml.safe_load(f)
    problems = []
    heads = spec.get("ad", {}).get("headlines", [])
    descs = spec.get("ad", {}).get("descriptions", [])
    if len(heads) < 3: problems.append(f"need >=3 headlines, got {len(heads)}")
    if len(descs) < 2: problems.append(f"need >=2 descriptions, got {len(descs)}")
    for h in heads:
        if len(h) > H_MAX: problems.append(f"headline too long ({len(h)}>{H_MAX}): {h!r}")
    for d in descs:
        if len(d) > D_MAX: problems.append(f"description too long ({len(d)}>{D_MAX}): {d!r}")
    if not spec.get("keywords"): problems.append("no keywords")
    if not spec.get("final_url"): problems.append("no final_url")
    if not spec.get("budget", {}).get("daily_inr"): problems.append("no budget.daily_inr")
    return spec, problems


def cmd_dry_run(args):
    spec, problems = load_spec(args.spec)
    b = spec.get("budget", {}); daily = b.get("daily_inr", 0)
    print(f"\n📋  {spec.get('name','(unnamed)')}")
    print(f"    status at launch : {spec.get('status','PAUSED')}")
    print(f"    budget           : ₹{daily}/day  (~₹{daily*14:,} over 14 days; Google monthly cap ≈ ₹{int(daily*30.4):,})")
    print(f"    bidding          : {spec.get('bidding',{}).get('strategy')}  max CPC ₹{spec.get('bidding',{}).get('max_cpc_inr')}")
    print(f"    schedule         : {spec.get('schedule',{}).get('start_date')} → {spec.get('schedule',{}).get('end_date')}")
    print(f"    geo              : {', '.join(spec.get('geo',{}).get('locations',[]))}")
    print(f"    languages        : {', '.join(spec.get('languages',[]))}")
    print(f"    final_url        : {spec.get('final_url')}")
    print(f"    keywords         : {len(spec.get('keywords',[]))}   negatives: {len(spec.get('negative_keywords',[]))}")
    print(f"    headlines        : {len(spec.get('ad',{}).get('headlines',[]))}   descriptions: {len(spec.get('ad',{}).get('descriptions',[]))}")
    if problems:
        print("\n❌  SPEC INVALID:")
        for p in problems: print(f"    - {p}")
        sys.exit(1)
    print("\n✅  Spec is valid and ready to launch. Add credentials, then:")
    print(f"    ./google_ads_cli.py launch {args.spec} --customer <CUSTOMER_ID>\n")


# ---------- Google client (lazy import so dry-run/help work without the library) ----------
def get_client(args):
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ImportError:
        sys.exit("google-ads library not installed. Run:  pip install -r requirements.txt")
    cfg = args.config or os.environ.get("GOOGLE_ADS_CONFIGURATION_FILE_PATH") or os.path.join(HERE, "google-ads.yaml")
    if not os.path.exists(cfg):
        sys.exit(f"No credentials file at {cfg}. Copy google-ads.yaml.example → google-ads.yaml and fill it "
                 f"(see SETUP_CREDENTIALS.md), or pass --config PATH.")
    return GoogleAdsClient.load_from_storage(cfg)


def cmd_check(args):
    client = get_client(args)
    svc = client.get_service("CustomerService")
    res = svc.list_accessible_customers()
    print("\n✅  Credentials work. Accessible ad accounts:")
    for rn in res.resource_names:
        print(f"    {rn.split('/')[-1]}   ({rn})")
    print("\nUse one of these customer IDs (digits only) as --customer.\n")


def _micros(inr):  return int(round(float(inr) * INR_MICROS))


def _resolve_geo(client, names):
    """Resolve human location names -> geoTargetConstant resource names."""
    svc = client.get_service("GeoTargetConstantService")
    req = client.get_type("SuggestGeoTargetConstantsRequest")
    req.locale = "en"; req.country_code = "IN"
    req.location_names.names.extend(names)
    out = []
    for s in svc.suggest_geo_target_constants(req).geo_target_constant_suggestions:
        out.append(s.geo_target_constant.resource_name)
    return out


# Google Ads language constant IDs
LANG_ID = {"english": "1000", "hindi": "1023"}


def cmd_launch(args):
    spec, problems = load_spec(args.spec)
    if problems:
        print("❌  Spec invalid — run dry-run first:"); [print("   -", p) for p in problems]; sys.exit(1)
    client = get_client(args)
    cid = args.customer.replace("-", "")

    budget_svc   = client.get_service("CampaignBudgetService")
    campaign_svc = client.get_service("CampaignService")
    adgroup_svc  = client.get_service("AdGroupService")
    crit_svc     = client.get_service("AdGroupCriterionService")
    camp_crit_svc= client.get_service("CampaignCriterionService")
    ad_svc       = client.get_service("AdGroupAdService")

    # 1) budget
    bop = client.get_type("CampaignBudgetOperation"); b = bop.create
    b.name = spec["name"] + f" budget {datetime.datetime.utcnow().timestamp():.0f}"
    b.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    b.amount_micros = _micros(spec["budget"]["daily_inr"])
    budget_rn = budget_svc.mutate_campaign_budgets(customer_id=cid, operations=[bop]).results[0].resource_name
    print("budget:", budget_rn)

    # 2) campaign (PAUSED, Search, manual CPC)
    cop = client.get_type("CampaignOperation"); c = cop.create
    c.name = spec["name"]
    c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    c.status = client.enums.CampaignStatusEnum.PAUSED
    c.campaign_budget = budget_rn
    c.manual_cpc.enhanced_cpc_enabled = False
    c.network_settings.target_google_search = True
    c.network_settings.target_search_network = False
    c.network_settings.target_content_network = False
    c.network_settings.target_partner_search_network = False
    sch = spec.get("schedule", {})
    if sch.get("start_date"): c.start_date = sch["start_date"].replace("-", "")
    if sch.get("end_date"):   c.end_date   = sch["end_date"].replace("-", "")
    campaign_rn = campaign_svc.mutate_campaigns(customer_id=cid, operations=[cop]).results[0].resource_name
    print("campaign:", campaign_rn, "(PAUSED)")

    # 3) geo + language targeting
    camp_ops = []
    for geo_rn in _resolve_geo(client, spec.get("geo", {}).get("locations", [])):
        op = client.get_type("CampaignCriterionOperation"); cc = op.create
        cc.campaign = campaign_rn; cc.location.geo_target_constant = geo_rn
        camp_ops.append(op)
    for lang in spec.get("languages", []):
        lid = LANG_ID.get(lang.strip().lower())
        if not lid: continue
        op = client.get_type("CampaignCriterionOperation"); cc = op.create
        cc.campaign = campaign_rn; cc.language.language_constant = f"languageConstants/{lid}"
        camp_ops.append(op)
    if camp_ops:
        camp_crit_svc.mutate_campaign_criteria(customer_id=cid, operations=camp_ops)
        print(f"targeting: {len(camp_ops)} geo+language criteria")

    # 4) ad group
    agop = client.get_type("AdGroupOperation"); ag = agop.create
    ag.name = spec.get("ad_group", {}).get("name", "ad-group")
    ag.campaign = campaign_rn
    ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    ag.status = client.enums.AdGroupStatusEnum.ENABLED
    ag.cpc_bid_micros = _micros(spec.get("bidding", {}).get("max_cpc_inr", 10))
    adgroup_rn = adgroup_svc.mutate_ad_groups(customer_id=cid, operations=[agop]).results[0].resource_name
    print("ad group:", adgroup_rn)

    # 5) keywords + negatives
    MATCH = client.enums.KeywordMatchTypeEnum
    kops = []
    for kw in spec.get("keywords", []):
        op = client.get_type("AdGroupCriterionOperation"); cr = op.create
        cr.ad_group = adgroup_rn
        cr.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        cr.keyword.text = kw["text"]
        cr.keyword.match_type = getattr(MATCH, kw.get("match", "PHRASE"))
        kops.append(op)
    for nk in spec.get("negative_keywords", []):
        op = client.get_type("AdGroupCriterionOperation"); cr = op.create
        cr.ad_group = adgroup_rn; cr.negative = True
        cr.keyword.text = nk["text"]
        cr.keyword.match_type = getattr(MATCH, nk.get("match", "BROAD"))
        kops.append(op)
    if kops:
        crit_svc.mutate_ad_group_criteria(customer_id=cid, operations=kops)
        print(f"keywords: {len(spec.get('keywords',[]))} + {len(spec.get('negative_keywords',[]))} negatives")

    # 6) responsive search ad
    aop = client.get_type("AdGroupAdOperation"); ada = aop.create
    ada.ad_group = adgroup_rn
    ada.status = client.enums.AdGroupAdStatusEnum.ENABLED
    ada.ad.final_urls.append(spec["final_url"])
    rsa = ada.ad.responsive_search_ad
    for h in spec["ad"]["headlines"]:
        a = client.get_type("AdTextAsset"); a.text = h; rsa.headlines.append(a)
    for d in spec["ad"]["descriptions"]:
        a = client.get_type("AdTextAsset"); a.text = d; rsa.descriptions.append(a)
    ad_rn = ad_svc.mutate_ad_group_ads(customer_id=cid, operations=[aop]).results[0].resource_name
    print("ad:", ad_rn)

    print(f"\n✅  Campaign created PAUSED. Review it in the Google Ads UI, then enable:")
    print(f"    ./google_ads_cli.py enable --customer {cid} --campaign {campaign_rn.split('/')[-1]}\n")


def cmd_report(args):
    client = get_client(args); cid = args.customer.replace("-", "")
    ga = client.get_service("GoogleAdsService")
    q = f"""
        SELECT campaign.name, campaign.status,
               metrics.impressions, metrics.clicks, metrics.cost_micros,
               metrics.ctr, metrics.average_cpc, metrics.conversions
        FROM campaign
        WHERE segments.date DURING LAST_{args.days}_DAYS
        ORDER BY metrics.cost_micros DESC"""
    print(f"\n📊  Last {args.days} days")
    print(f"    {'campaign':30} {'status':9} {'impr':>7} {'clicks':>7} {'cost₹':>8} {'CTR':>6} {'avgCPC₹':>8} {'conv':>5}")
    any_row = False
    for row in ga.search(customer_id=cid, query=q):
        any_row = True
        m = row.metrics
        print(f"    {row.campaign.name[:30]:30} {row.campaign.status.name:9} "
              f"{m.impressions:7d} {m.clicks:7d} {m.cost_micros/INR_MICROS:8.0f} "
              f"{m.ctr*100:5.1f}% {m.average_cpc/INR_MICROS:8.1f} {m.conversions:5.0f}")
    if not any_row:
        print("    (no data yet — campaign may be paused or just started)")
    print()


def cmd_search_terms(args):
    """The payoff: the ACTUAL queries people typed to trigger your ads — the buyer's real vocabulary."""
    client = get_client(args); cid = args.customer.replace("-", "")
    ga = client.get_service("GoogleAdsService")
    q = f"""
        SELECT search_term_view.search_term,
               metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions
        FROM search_term_view
        WHERE segments.date DURING LAST_{args.days}_DAYS
        ORDER BY metrics.clicks DESC, metrics.impressions DESC"""
    print(f"\n🔎  Search terms — the actual queries people typed (last {args.days} days)")
    print(f"    {'query':45} {'impr':>6} {'clicks':>7} {'cost₹':>7} {'conv':>5}")
    rows = list(ga.search(customer_id=cid, query=q))
    if not rows:
        print("    (no search-term data yet — needs a few days of live traffic)\n"); return
    for row in rows:
        m = row.metrics; t = row.search_term_view.search_term
        print(f"    {t[:45]:45} {m.impressions:6d} {m.clicks:7d} {m.cost_micros/INR_MICROS:7.0f} {m.conversions:5.0f}")
    print(f"\n    → the queries with clicks are your buyers' real words. Reuse them in SEO, the landing, Rohan's pitch.\n")


def _set_campaign_status(args, status_name):
    client = get_client(args); cid = args.customer.replace("-", "")
    svc = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation"); c = op.update
    c.resource_name = client.get_service("CampaignService").campaign_path(cid, args.campaign)
    c.status = getattr(client.enums.CampaignStatusEnum, status_name)
    client.copy_from(op.update_mask, client.get_type("FieldMask")); op.update_mask.paths.append("status")
    svc.mutate_campaigns(customer_id=cid, operations=[op])
    print(f"campaign {args.campaign} -> {status_name}")


def main():
    p = argparse.ArgumentParser(description="TrigunAI Google Ads pipeline")
    p.add_argument("--config", help="path to google-ads.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("dry-run"); sp.add_argument("spec"); sp.set_defaults(fn=cmd_dry_run)
    sp = sub.add_parser("check"); sp.set_defaults(fn=cmd_check)
    sp = sub.add_parser("launch"); sp.add_argument("spec"); sp.add_argument("--customer", required=True); sp.set_defaults(fn=cmd_launch)
    sp = sub.add_parser("report"); sp.add_argument("--customer", required=True); sp.add_argument("--days", type=int, default=14); sp.set_defaults(fn=cmd_report)
    sp = sub.add_parser("search-terms"); sp.add_argument("--customer", required=True); sp.add_argument("--days", type=int, default=14); sp.set_defaults(fn=cmd_search_terms)
    sp = sub.add_parser("pause"); sp.add_argument("--customer", required=True); sp.add_argument("--campaign", required=True); sp.set_defaults(fn=lambda a: _set_campaign_status(a, "PAUSED"))
    sp = sub.add_parser("enable"); sp.add_argument("--customer", required=True); sp.add_argument("--campaign", required=True); sp.set_defaults(fn=lambda a: _set_campaign_status(a, "ENABLED"))

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
