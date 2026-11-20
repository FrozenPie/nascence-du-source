import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import symbol_evolution as se
seen = []
async def fake(urls, sp, up, **k):
    seen.append(up); return {"tablet": "x"}
se.call_node_json = fake
se.memory_store.store_symbol_tablet = lambda *a: "id"
eng = se.SymbolEvolutionEngine.__new__(se.SymbolEvolutionEngine); eng._base_urls = []
for created, expect_prior in ((se._LEGACY_TABLET_CUTOFF_TS - 10, False), (se._LEGACY_TABLET_CUTOFF_TS + 10, True)):
    se.memory_store.get_symbol_tablets = lambda s, limit=1, c=created: [{"tablet": "OLDTEXT", "created": c}]
    seen.clear(); asyncio.run(eng.write_tablet(None, "fire", 0.5, "ctx"))
    assert ("OLDTEXT" in seen[0]) == expect_prior, (created, seen)
print("ok")
