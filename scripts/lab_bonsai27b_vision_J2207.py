import base64, io, json, time, urllib.request, pathlib
from PIL import Image, ImageDraw
OUT = pathlib.Path(__file__).resolve().parents[1] / "docs/lab/bonsai27b_J-2207"
last = open(r"C:\Nascence\data\nascence.log", "rb").read()[-300:].decode("utf-8", "replace").strip().splitlines()[-1]
assert "Nascence shutting down." in last, last
im = Image.new("RGB", (256, 256), (30, 60, 160)); d = ImageDraw.Draw(im)
d.ellipse((70, 70, 190, 190), fill=(220, 30, 30)); d.rectangle((20, 200, 236, 240), fill=(240, 220, 40))
buf = io.BytesIO(); im.save(buf, "PNG"); im.save(OUT / "vision_still_J-2207.png")
body = {"model": "MichelRosselli/bonsai-27b:latest", "stream": False, "think": False, "keep_alive": "5m",
        "messages": [{"role": "user", "content": "Describe this image: shapes and colours.", "images": [base64.b64encode(buf.getvalue()).decode()]}],
        "options": {"temperature": 0, "num_predict": 120, "num_ctx": 4096}}
t = time.time()
try:
    r = urllib.request.Request("http://127.0.0.1:11433/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(r, timeout=300).read())
    res = {"truth": "blue background, red circle centre, yellow bar at bottom", "reply": d["message"]["content"], "wall": round(time.time()-t, 2), "prompt_tok": d.get("prompt_eval_count")}
except urllib.error.HTTPError as e:
    res = {"error": e.read().decode()[:600], "wall": round(time.time()-t, 2)}
except Exception as e:
    res = {"error": repr(e)[:600]}
print(res); (OUT / "vision_J-2207.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
