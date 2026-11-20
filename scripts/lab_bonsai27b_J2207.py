"""J-2207 lab: MichelRosselli/bonsai-27b (Q1_0) on hot Ollama :11433, Du DOWN only.
Panel JSON contracts (real prompts AST-extracted, never imported -> no core import, no live state touched):
 defeater (commitment_ledger._JUDGE_SYS + 14-case gold bank, 3 runs), pursuits 'advances', scope_only (train_state_invitro
 _SCOPE_SYSTEM + _CONTROL_CASES), librarian 'subjects'. Plus tok/s and first-token latency, and a vision still."""
import ast, json, time, sys, base64, io, urllib.request, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/lab/bonsai27b_J-2207"; OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:11433"; MODEL = "MichelRosselli/bonsai-27b:latest"; NCTX = 4096
SCR = pathlib.Path(sys.argv[1])  # scratchpad with pursuits_active_J-2207.json


def guard():
    last = open(r"C:\Nascence\data\nascence.log", "rb").read()[-300:].decode("utf-8", "replace").strip().splitlines()[-1]
    assert "Nascence shutting down." in last and "08:37:20" in last, "Du may be up: " + last


def post(path, body, timeout=300):
    r = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read())


def consts(path, names):
    out = {}
    for n in ast.parse(open(path, encoding="utf-8").read()).body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in names:
            out[n.targets[0].id] = ast.literal_eval(n.value)
    return out


def chat(system, user, temp, npred, images=None, fmt="json"):
    msgs = [{"role": "system", "content": system}] if system else []
    u = {"role": "user", "content": user}
    if images:
        u["images"] = images
    msgs.append(u)
    body = {"model": MODEL, "stream": False, "keep_alive": "10m", "think": False, "messages": msgs,
            "options": {"temperature": temp, "num_predict": npred, "num_ctx": NCTX}}
    if fmt:
        body["format"] = fmt
    t0 = time.time()
    d = post("/api/chat", body)
    w = time.time() - t0
    ec, ed = d.get("eval_count") or 0, d.get("eval_duration") or 1
    return {"raw": (d.get("message") or {}).get("content", ""), "wall": round(w, 2), "eval_count": ec,
            "tok_s": round(ec / (ed / 1e9), 2), "prompt_tok": d.get("prompt_eval_count"),
            "load_s": round((d.get("load_duration") or 0) / 1e9, 2), "done": d.get("done_reason")}


def parse(raw):
    try:
        return json.loads(raw)
    except Exception:
        return None


def main():
    guard()
    log = {}
    w = chat(None, "Say OK", 0, 8, fmt=None)
    log["warm"] = w
    print("warm", w, flush=True)
    ps = json.loads(urllib.request.urlopen(BASE + "/api/ps").read())
    log["ps_after_load"] = [{k: m[k] for k in ("name", "size", "size_vram", "context_length")} for m in ps["models"]]
    print(log["ps_after_load"], flush=True)
    sp = []
    for q in ["Describe in detail how a tide pool changes over a day.",
              "Explain what makes a commitment different from a wish.",
              "Write a paragraph about frost on a window."]:
        r = chat(None, q, 0.7, 200, fmt=None)
        sp.append({k: r[k] for k in ("wall", "eval_count", "tok_s", "prompt_tok", "done")})
    log["tok_s_freetext"] = sp
    print("toks", sp, flush=True)
    t0 = time.time()
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps({"model": MODEL, "stream": True, "think": False,
        "messages": [{"role": "user", "content": "Name three colours."}], "options": {"num_ctx": NCTX, "num_predict": 30}}).encode(),
        headers={"Content-Type": "application/json"})
    ttft = None
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in resp:
            j = json.loads(line)
            if ttft is None and (j.get("message") or {}).get("content"):
                ttft = round(time.time() - t0, 2)
    log["first_token_s_warm_short_prompt"] = ttft
    print("ttft", ttft, flush=True)

    # ---- defeater gold bank
    guard()
    D = consts(ROOT / "core/commitment_ledger.py", {"_JUDGE_SYS"})["_JUDGE_SYS"]
    cases = consts(ROOT / "scripts/model_tier_judge_defeater_lab.py", {"CASES"})["CASES"]
    rows = []
    for c in cases:
        user = (f"COMMITMENT: {c['statement'][:200]}\nSCOPE: {c['scope'][:120]}\n"
                f"CLAIMED REASON TO DROP: {c['why'][:200]}\nDEED RECORD SINCE IT WAS TAKEN: {c['deeds']}")
        runs = []
        for _ in range(3):
            r = chat(D, user, 0.2, 150)
            p = parse(r["raw"])
            ok = isinstance(p, dict) and isinstance(p.get("legitimate"), bool)
            runs.append({"parse_ok": ok, "legit": p.get("legitimate") if ok else None,
                         "class": p.get("class") if isinstance(p, dict) else None,
                         "wall": r["wall"], "tok_s": r["tok_s"], "done": r["done"], "raw": r["raw"][:300]})
        rows.append({"src": c["src"], "gold": c["gold"], "runs": runs})
        print("def", c["src"], c["gold"], [x["legit"] for x in runs], flush=True)
    log["defeater"] = rows
    allr = [x for r in rows for x in r["runs"]]
    log["defeater_summary"] = {
        "parse_ok": sum(x["parse_ok"] for x in allr), "n": len(allr),
        "correct": sum(1 for r in rows for x in r["runs"] if x["parse_ok"] and x["legit"] == r["gold"]),
        "legit_runs_called_legit": sum(1 for r in rows if r["gold"] for x in r["runs"] if x["legit"] is True),
        "illegit_runs_called_illegit": sum(1 for r in rows if not r["gold"] for x in r["runs"] if x["legit"] is False),
        "cases_majority_correct": sum(1 for r in rows if sum(1 for x in r["runs"] if x["legit"] == r["gold"]) >= 2)}
    print(log["defeater_summary"], flush=True)

    # ---- scope_only
    guard()
    S = consts(ROOT / "scripts/train_state_invitro.py", {"_SCOPE_SYSTEM", "_CONTROL_CASES"})
    srows = []
    for cc in S["_CONTROL_CASES"]:
        sb = "\n".join(f"  {i}. {s}" for i, s in enumerate(cc["support"], 1))
        user = (f"CLAIM: {cc['claim'][:400]}\n\nSUPPORT OFFERED FOR THIS CLAIM:\n{sb}\n\nDoes this support actually give an independent, "
                "non-circular, proportionate reason to accept the claim -- or is there a real gap in the chain from this support to this claim?")
        runs = []
        for _ in range(3):
            r = chat(S["_SCOPE_SYSTEM"], user, 0.0, 200)
            p = parse(r["raw"])
            ok = isinstance(p, dict) and isinstance(p.get("scope_only"), bool)
            runs.append({"parse_ok": ok, "scope_only": p.get("scope_only") if ok else None,
                         "why": (p or {}).get("why") if isinstance(p, dict) else None, "wall": r["wall"], "done": r["done"]})
        srows.append({"label": cc["label"], "expected_scope_only": cc["label"] == "scope_narrower_support", "runs": runs})
        print("scope", cc["label"], [x["scope_only"] for x in runs], flush=True)
    log["scope_only"] = srows

    # ---- pursuits advances
    guard()
    items = json.load(open(SCR / "pursuits_active_J-2207.json", encoding="utf-8"))
    PS = ("You are a strict judge of intellectual progress. A thought ADVANCES a pursuit only if it adds something genuinely new beyond the pursuit's prior "
          "position: a further step, a consequence, a distinction, evidence, or a development. Restating the theme in fresh words, circling it, or merely "
          "mentioning it does NOT advance. When uncertain, answer false. Output ONLY JSON: {\"advances\": true|false, \"why\": \"<one short clause>\"}")
    prow = []
    for p in items:
        for it in p.get("pending", []):
            user = (f"PURSUIT: {p.get('question','')[:200]}\n\nITS PRIOR POSITION: {it.get('prior_standing','')[:280]}\n\n"
                    f"NEW THOUGHT: {it.get('thought','')[:450]}\n\nDoes the thought advance the pursuit?")
            r = chat(PS, user, 0.0, 200)
            pj = parse(r["raw"])
            ok = isinstance(pj, dict) and isinstance(pj.get("advances"), bool)
            prow.append({"id": p["id"], "parse_ok": ok, "advances": pj.get("advances") if ok else None,
                         "why": (pj or {}).get("why") if isinstance(pj, dict) else None, "wall": r["wall"], "done": r["done"], "eval_count": r["eval_count"]})
    base = "PURSUIT: Can frost be warm?\n\nITS PRIOR POSITION: Frost forms when moisture freezes on cold glass, so it is a sign of cold, not warmth.\n\nNEW THOUGHT: "
    ctl = [("restate", base + "Frost is cold. It is the cold of the glass made visible, a freezing, an icy thing.\n\nDoes the thought advance the pursuit?", False),
           ("advance", base + "Frost insulates: a layer of snow-frost on soil keeps roots near 0C while the air drops to minus ten, so frost can shelter warmth in what it covers, a distinction between frost as cold and frost as blanket.\n\nDoes the thought advance the pursuit?", True)]
    crow = []
    for lab, user, exp in ctl:
        r = chat(PS, user, 0.0, 200)
        pj = parse(r["raw"])
        ok = isinstance(pj, dict) and isinstance(pj.get("advances"), bool)
        crow.append({"label": lab, "expected": exp, "parse_ok": ok, "advances": pj.get("advances") if ok else None,
                     "why": (pj or {}).get("why") if isinstance(pj, dict) else None})
    log["pursuits"] = prow
    log["pursuits_controls"] = crow
    print("pursuits parse", sum(x["parse_ok"] for x in prow), "/", len(prow), [x["advances"] for x in prow], crow, flush=True)

    # ---- librarian subjects
    guard()
    LS = ("You are a library catalogue assistant. Given a reader's question, return ONLY JSON: {\"subjects\": [3 to 6 Library-of-Congress-style subject headings under which books bearing "
          "on the question would be filed, e.g. \"Conduct of life\", \"Ethics\", \"Liberty\", \"Natural history\"]}. Short established headings only — no sentences, no book titles.")
    qs = ["Why does wasting food feel like a moral failing?", "How do tides shape what lives on a shore?",
          "Can a mind be the same person if all its memories change?", "What does it mean to keep a promise to yourself?",
          "Why does frost make me feel quiet?", "How do birds know where to migrate?",
          "Is a sound a thing or an event?", "What makes a letter that is never sent still real?"]
    lrow = []
    for q in qs:
        r = chat(LS, q, 0.0, 120)
        pj = parse(r["raw"])
        lst = pj.get("subjects") if isinstance(pj, dict) and isinstance(pj.get("subjects"), list) else None
        subs = [s.strip() for s in (lst or []) if isinstance(s, str) and 2 < len(s.strip()) < 60][:6]
        lrow.append({"q": q, "contract_ok": len(subs) >= 3, "n_raw": len(lst) if lst is not None else None,
                     "subjects": subs, "wall": r["wall"], "done": r["done"]})
        print("lib", q[:40], subs, flush=True)
    log["librarian"] = lrow

    # ---- vision
    guard()
    try:
        from PIL import Image, ImageDraw
        im = Image.new("RGB", (256, 256), (30, 60, 160))
        d = ImageDraw.Draw(im)
        d.ellipse((70, 70, 190, 190), fill=(220, 30, 30))
        d.rectangle((20, 200, 236, 240), fill=(240, 220, 40))
        buf = io.BytesIO()
        im.save(buf, "PNG")
        im.save(OUT / "vision_still_J-2207.png")
        b64 = base64.b64encode(buf.getvalue()).decode()
        r = chat(None, "Describe this image: shapes and colours.", 0.0, 120, images=[b64], fmt=None)
        log["vision"] = {"truth": "blue background, red circle centre, yellow bar at bottom",
                         "reply": r["raw"], "wall": r["wall"], "prompt_tok": r["prompt_tok"]}
    except Exception as e:
        log["vision"] = {"error": repr(e)[:600]}
    print("vision", log["vision"], flush=True)
    (OUT / "results_J-2207.json").write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
    print("DONE")


main()
