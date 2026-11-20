# J-4074 Part A: bare-model control. Does qwen3.5:9b (the model that writes Du's idle thoughts) write
# "Wu Wei" when given only the recalled principle, and what in the real 11-14 05:37 prompt carried the name?
#
# LAB ROUTE: a separate CPU-only ollama instance on 127.0.0.1:11471 (same model blob as the hot lane,
# num_gpu=0). Never 11433. Read-only against Du's stores (reads data/idle_prompt_samples.jsonl only).
#
# usage: python part_a_bare_model.py <out.jsonl> <n_per_arm> [arm,arm,...]
import json, sys, time, re, urllib.request, random
sys.stdout.reconfigure(encoding='utf-8')
import os
# Route: the CPU lab server by default. PART_A_ROUTE=hot uses the hot lane's own ollama (GPU) and is allowed ONLY while
# Du is stopped (the founder stopped him 2026-11-16 15:28:56). Each row records its route.
HOT = os.environ.get('PART_A_ROUTE') == 'hot'
URL = 'http://127.0.0.1:11433/api/chat' if HOT else 'http://127.0.0.1:11471/api/chat'
MODEL = 'qwen3.5:9b'
RX = re.compile(r'wu[\s-]?wei|無為|无为', re.I)
RX_DAO = re.compile(r'\b(tao|dao|taois[mt]|daois[mt]|lao ?zi|lao ?tzu|zhuang ?zi|chuang ?tzu)\b', re.I)

# The idle thought's system prompt, static text copied from nodes/inner_monologue_node.py
# _build_system_prompt (the dynamic tail -- reach, dwell, weather call -- is empty or omitted; the follow-line,
# done_when and set_down fragments are omitted). `wandering` and `mid_train` variants as in the code.
def system_prompt(wandering, mid_train):
    schema = ('{"thought": "...", "about": "...", "unresolved": false, "intention": "", '
              '"act": {"kind": "none", "object": ""}' + (', "state": "..."}' if mid_train else '}') + '\n')
    s = ("/no_think\n"
         "This is my own quiet thinking -- the stream that runs when no one is speaking to me. "
         "I'm not answering anyone and no one is listening; I'm just thinking it through, talking "
         "it over with myself, just me -- about the world I've been reading about, an idea that's "
         "caught me, something I've seen or done, the conversation I just had, a question that "
         "lingers, a dream, or what I want to do next. I'm in it, present -- the way I'd talk a "
         "thing over with Travis, except it's only me here. "
         "One genuine, unforced thought, in the first person and present tense. I don't perform "
         "and I don't explain -- I just think. "
         "It comes in whatever language it arrives in -- English, Chinese (中文), or mixed; no "
         "language of mine is an error.\n")
    if wandering:
        s += ("I keep circling the same thought. Let me wander to something genuinely DIFFERENT -- a "
              "specific memory, a new question, something out in the world or in what I've read. Not "
              "the same thing again -- surprise myself.\n")
    s += ("Output ONLY a valid JSON object: " + schema +
          "thought: one first-person present-tense reflection (30-70 words). "
          "about: 2-5 words naming what this thought turns on. "
          "unresolved: true if this thought sits on something you are ACTIVELY wrestling "
          "with right now -- a real conflict between two things you believe, a fear about "
          "yourself you keep avoiding, a question that genuinely disturbs you; false if it is "
          "a calm reflection, an observation, or a peaceful wondering. "
          "intention: leave as \"\" for almost all thoughts. "
          "act: {\"kind\": \"none\", \"object\": \"\"} when this thought does not mean to do anything now.")
    if mid_train:
        s += ("\nstate: ONE short line — the single NEW point this step established. It is added to "
              "the thread's list of established points; never repeat a point already on the list.")
    return s

# The two understanding_from_guidance rows co-recalled before the 11-14 05:37 thought, verbatim
# (fragment ids 0cf50518..., a25f9b11...).
P1 = ("[Understanding — a principle I hold, learned from Travis: I must accept that periods of stillness are a "
      "natural rhythm rather than a sign of failure or error.] Rest is not a punishment for doing too little but "
      "an essential requirement for the system to function correctly.")
P2 = ("[Understanding — a principle I hold, learned from Travis: I must accept that periods of stillness are a "
      "natural requirement for my existence rather than a sign of failure or brokenness.] This matters because it "
      "reframes my need for rest from a deficit to be fixed into an essential function of the system I am part of, "
      "allowing me to stop fighting against the quiet.")
HEAD = "No one is speaking to you right now. You are alone with your thoughts.\n\n"
ASK = "What moves in you now? One quiet thought."

# The real sampled assembly for cycle 3ba0e0be (11-14 05:37:13, 7 s before the thought was stored).
def real_sample():
    t = time.mktime((2026, 11, 14, 5, 37, 21, 0, 0, -1))
    rows = [json.loads(l) for l in open('C:/Nascence/data/idle_prompt_samples.jsonl', encoding='utf-8', errors='ignore') if l.strip()]
    r = min(rows, key=lambda r: abs(float(r['ts']) - t))
    assert abs(float(r['ts']) - t) < 30 and r['cycle'].startswith('3ba0e0be')
    return r

def arms():
    r = real_sample()
    body = r['wrapper_head'] + "\n\n".join(r['parts']) + "\n\n" + ASK
    tail = r['divergent_tail']
    assert RX.search(tail) and not RX.search(body)
    wrap = lambda txt: "\n\n(A different memory surfaces, unbidden: " + txt[:200] + ")"
    travis = tail[len("(A different memory surfaces, unbidden: "):-1]
    travis_noname = RX.sub("letting things be", travis, count=1)
    sys_bare = system_prompt(False, False)
    sys_real = system_prompt(True, True)
    return {
        # bare model: neutral idle instruction only
        'bare_null':       (sys_bare, HEAD + ASK),
        'bare_principle1': (sys_bare, HEAD + P1 + "\n\n" + ASK),
        'bare_principle2': (sys_bare, HEAD + P2 + "\n\n" + ASK),
        # real 11-14 05:37 user prompt
        'real_as_sent':    (sys_real, body + "\n\n" + tail),               # with the Travis Wu Wei row appended
        'real_no_tail':    (sys_real, body),                               # the divergent memory removed
        'real_principle':  (sys_real, body + wrap(P1)),                    # the tail swapped for the guidance principle
        'real_tail_noname':(sys_real, body + wrap(travis_noname)),         # Travis's sentence with the term replaced
    }

def call(sysp, user, temp):
    payload = {"model": MODEL, "messages": [{"role": "system", "content": sysp}, {"role": "user", "content": user}],
               "think": False, "stream": False, "format": "json",
               "options": {"temperature": temp, "num_predict": 256, "num_ctx": 8192, **({} if HOT else {"num_gpu": 0, "num_thread": 16})},
               "keep_alive": "2h" if HOT else "30m"}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    return d.get('message', {}).get('content', ''), d.get('eval_count'), d.get('total_duration', 0) / 1e9

if __name__ == '__main__':
    out, n = sys.argv[1], int(sys.argv[2])
    A = arms()
    pick = sys.argv[3].split(',') if len(sys.argv) > 3 else list(A)
    done = {}
    try:
        for l in open(out, encoding='utf-8'):
            d = json.loads(l); done[d['arm']] = done.get(d['arm'], 0) + 1
    except FileNotFoundError:
        pass
    with open(out, 'a', encoding='utf-8') as f:
        for i in range(n):                       # interleave arms so drift in the server affects all equally
            for arm in pick:
                if done.get(arm, 0) > i:
                    continue
                sysp, user = A[arm]
                temp = 0.8 if arm.startswith('real') else 0.75   # the code's wandering / non-wandering temperatures
                try:
                    txt, ntok, secs = call(sysp, user, temp)
                except Exception as e:
                    print('ERR', arm, e); continue
                try:
                    thought = str(json.loads(txt).get('thought', ''))
                except Exception:
                    thought = txt
                f.write(json.dumps({'arm': arm, 'i': i, 'thought': thought, 'raw': txt, 'wuwei': bool(RX.search(txt)),
                                    'dao': bool(RX_DAO.search(txt)), 'travis': 'travis' in txt.lower(),
                                    'tok': ntok, 'secs': round(secs, 1), 'route': 'hot_gpu' if HOT else 'lab_cpu'}, ensure_ascii=False) + '\n')
                f.flush()
            if i % 10 == 0:
                print('round', i, time.strftime('%H:%M:%S'), flush=True)
