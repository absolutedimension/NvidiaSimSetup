import urllib.request, urllib.parse, json, ssl, time
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
AJAX="https://bpsc.bihar.gov.in/wp-admin/admin-ajax.php"; NONCE="8484a26a88"
def pdfs(iid):
    body=urllib.parse.urlencode({"action":"get_question_booklets_pdfs","item_id":iid,"nonce":NONCE}).encode()
    req=urllib.request.Request(AJAX, body, headers={"User-Agent":"Mozilla/5.0","X-Requested-With":"XMLHttpRequest","Referer":"https://bpsc.bihar.gov.in/question-booklets/"})
    r=urllib.request.urlopen(req, context=ctx, timeout=40); d=json.loads(r.read().decode())
    return (d.get("data") or {}).get("pdfs",[]) if d.get("success") else []
labels={63:"66th Prelims",60:"67th Prelims",61:"67th Prelims Re-Exam",27:"68th Prelims",24:"69th Prelims",97:"71st Prelims"}
for nid,lab in labels.items():
    print(f"\n===== {lab} (node {nid}) =====")
    for f in pdfs(nid):
        print(f"  {f.get('title')}  ->  {f.get('url')}")
