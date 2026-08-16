import urllib.request, urllib.parse, json, ssl, os
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
AJAX="https://bpsc.bihar.gov.in/wp-admin/admin-ajax.php"; NONCE="8484a26a88"
def pdfs(iid):
    body=urllib.parse.urlencode({"action":"get_question_booklets_pdfs","item_id":iid,"nonce":NONCE}).encode()
    req=urllib.request.Request(AJAX, body, headers={"User-Agent":"Mozilla/5.0","X-Requested-With":"XMLHttpRequest","Referer":"https://bpsc.bihar.gov.in/question-booklets/"})
    r=urllib.request.urlopen(req, context=ctx, timeout=40); d=json.loads(r.read().decode())
    return (d.get("data") or {}).get("pdfs",[]) if d.get("success") else []
targets={"66th":63,"67th":60,"67th_reexam":61,"68th":27,"69th":24,"71st":97}
base=os.path.expanduser("~/drop/bpsc")
for name,nid in targets.items():
    for f in pdfs(nid):
        if "general studies" not in (f.get("title") or "").lower(): continue
        url=f.get("file_url"); 
        if not url: print(name,"NO URL"); continue
        d=os.path.join(base,name); os.makedirs(d,exist_ok=True)
        dest=os.path.join(d,f"GS_{name}.pdf")
        req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        try:
            data=urllib.request.urlopen(req, context=ctx, timeout=120).read()
            open(dest,"wb").write(data)
            print(f"{name}: {len(data)//1024} KB  <- {url}  head={data[:5]}")
        except Exception as e:
            print(name,"ERR",e,url)
