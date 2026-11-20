import os, json, sys
d = r"C:/Nascence/data"
o = {f: (os.stat(os.path.join(d, f)).st_size) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))}
p = sys.argv[1]
if sys.argv[2] == "save":
    json.dump(o, open(p, "w"))
    print("saved", len(o))
else:
    b = json.load(open(p))
    ch = {f: (b.get(f), o.get(f)) for f in set(b) | set(o) if b.get(f) != o.get(f)}
    print("files", len(o), "size-changed/added/removed:", len(ch))
    for f, v in list(ch.items())[:25]:
        print(" ", f, v)
