import urllib.request, urllib.parse, json, ssl, sys, time
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
AJAX="https://bpsc.bihar.gov.in/wp-admin/admin-ajax.php"
NONCE="8484a26a88"
def post(data):
    body=urllib.parse.urlencode(data).encode()
    req=urllib.request.Request(AJAX, body, headers={"User-Agent":"Mozilla/5.0","X-Requested-With":"XMLHttpRequest","Referer":"https://bpsc.bihar.gov.in/question-booklets/"})
    for _ in range(3):
        try:
            r=urllib.request.urlopen(req, context=ctx, timeout=40)
            return json.loads(r.read().decode())
        except Exception as e:
            time.sleep(2); last=e
    print("ERR",last); return {}
def children(pid):
    d=post({"action":"get_children","parent_id":pid,"nonce":NONCE})
    return (d.get("data") or {}).get("children",[]) if d.get("success") else []
def pdfs(iid):
    d=post({"action":"get_question_booklets_pdfs","item_id":iid,"nonce":NONCE})
    return (d.get("data") or {}).get("pdfs",[]) if d.get("success") else []
out=[]
def walk(pid, path, depth=0):
    for c in children(pid):
        cid=c.get("id"); title=(c.get("title") or "").strip()
        p=path+[title]
        hp=c.get("has_pdfs") in (1,"1",True); hc=c.get("has_children") in (1,"1",True)
        print("  "*depth+f"[{cid}] {title}  {'PDFS' if hp else ''}{'>' if hc else ''}")
        if hp:
            for f in pdfs(cid):
                out.append({"path":" / ".join(p),"title":f.get("title"),"url":f.get("url")})
        if hc and depth<5:
            walk(cid, p, depth+1)
walk(0,[])
json.dump(out, open("/tmp/qb_files.json","w"), indent=1)
print("\nTOTAL PDF FILES:",len(out))
