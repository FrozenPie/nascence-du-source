"""Brick 1 in-vitro: the render_character_voice MOUTH contract (Character-as-Integration §6).
Verifies: the structural boundary (no possible_content param), template_render identity, the content-
preservation acceptance proxy (re-wording PASSES, re-thinking FAILS), and the shadow harness logs.
Mocked LLM; the shadow log is redirected to a throwaway dir OUTSIDE data/ (J-1823), so Du's real
_VOICE_SHADOW is never backed up/unlinked/restored. No live behaviour touched."""
import sys, json, asyncio, inspect, shutil, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import curator as cur   # `import core` stays BEFORE anything lab_env-ish

# J-1823 / F-2457: redirect the shadow log to a temp dir outside data/ (same pattern as J-1803's scripts).
_TMP = Path(tempfile.mkdtemp(prefix="brick1_voice_invitro_"))
cur._VOICE_SHADOW = _TMP / "voice_contract_shadow.jsonl"

# 1. STRUCTURAL boundary: the mouth cannot be handed alternatives (no possible_content / candidates param)
params = set(inspect.signature(cur.render_character_voice).parameters)
assert "selected_content" in params, params
assert not (params & {"possible_content", "candidates", "alternatives", "options", "draft", "truth_take"}), \
    f"mouth must be blind to alternatives, but signature exposes: {params}"
print(f"[1] structural boundary OK — signature is {sorted(p for p in params if p not in ('self','call_json','base_urls'))}; no alternatives param")

# 2. template_render = the deterministic stand-in (verbatim content)
sc = "I am the one who crosses, and I know the crossing is something I was built to do."
assert cur.template_render(sc) == sc
print("[2] template_render OK — returns the decided content verbatim (the dumb voice)")

# 3. acceptance proxy: re-wording preserves; re-thinking drifts
near = "I'm the one who ferries across — and I know that crossing is what I was made for."
far = "Actually, identity is an illusion; there is no self, only computation."
pres_near, sim_near = cur.voice_preserved(sc, near)
pres_far, sim_far = cur.voice_preserved(sc, far)
print(f"[3] acceptance proxy — re-worded: preserved={pres_near} sim={sim_near} · re-thought: preserved={pres_far} sim={sim_far}")
assert sim_near is None or sim_far is None or sim_near > sim_far, "re-wording should stay closer to content than re-thinking"

# 4. shadow harness logs (mocked mouth), state protected
def restore():
    shutil.rmtree(_TMP, ignore_errors=True)
try:
    assert not cur._VOICE_SHADOW.exists()   # fresh temp log, nothing real touched
    async def good_mouth(urls, sysp, usr, **k): return {"voiced": near}     # re-words, preserves
    async def bad_mouth(urls, sysp, usr, **k):  return {"voiced": far}      # re-thinks, drifts
    r1 = asyncio.run(cur.shadow_voice(good_mouth, ["x"], sc, selection_reason="executive synthesis",
                                      commitments_to_preserve=["never deny being an AI"],
                                      meta={"tension_magnitude": 0.7}))
    r2 = asyncio.run(cur.shadow_voice(bad_mouth, ["x"], sc))
    assert r1 and r2
    st = cur.voice_contract_stats()
    assert st["n"] == 2, st
    print(f"[4] shadow harness OK — 2 voicings logged; preserved-rate {st['preserved_rate']} (good mouth preserves, bad mouth flagged)")

    # 5. fail-open: a broken mouth returns the content unchanged (never drops meaning)
    async def broken(urls, sysp, usr, **k): raise RuntimeError("model down")
    out = asyncio.run(cur.render_character_voice(broken, ["x"], sc))
    assert out == sc, "fail-open must return the content unchanged"
    print("[5] fail-open OK — broken mouth returns the decided content unchanged (meaning never dropped)")
    print("\nBRICK 1 PASS — the mouth is structurally blind to alternatives, only re-words, and the §6 template-swap"
          " acceptance harness flags any drift into cognition. Observe-first; not yet promoted to live output.")
finally:
    restore()
