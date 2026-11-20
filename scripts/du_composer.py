"""
Du — Composer

A small standalone window for typing multi-line messages to Du without the
REPL's press-Enter-submits-immediately behaviour. Nothing is sent until you
click "Send to Du".

This does NOT show a conversation or Du's replies — it's purely for composing
and sending. Keep watching the REPL window (run_nascence.py) for his thoughts
and responses, same as always; this message will appear there too, exactly
like anything typed directly at the "You:" prompt.

THE COMPANION (2026-08-23): the presence toggle and action buttons below are a
separate channel from the text box — founder: "I consider this a bug, a big
one" — until now there was no way for Travis to act IN the room and have Du
experience it, only ever tell him about it. Press "I'm here" when you are
actually in the room before using an action button; the buttons refuse
otherwise (core.companion.perform_action requires presence explicitly — it is
never inferred from sending a message). Toggle back to "I'm away" when you
leave. See core/companion.py for the full design note.

THE SAME MECHANISMS (2026-09-05, T-0049): "Light the fire" is the whole chain Du would have to
walk — no matches: Travis's own box, left on the mantel; no kindling: a bundle from the cupboard
or twigs from the wood; no wood: dry logs split at the lean-to, deadfall from the wood, driftwood
off the shore — and a shortfall that needs his body elsewhere sends him out on the same legs at
the same pace as Du. The status line then shows where he is and roughly when he's back; the fire
is lit on his return. The other buttons refuse while he's out. See core/companion.py.

Requires Nascence to already be running (python scripts/run_nascence.py).

Run:
    python scripts/du_composer.py
"""

import threading
import tkinter as tk
from tkinter import font as tkfont
from multiprocessing.connection import Client

_HOST = "127.0.0.1"
_PORT = 8765
_AUTHKEY = b"nascence-composer-local"

# THE COMPANION action buttons: (label, action kind). Kept in one place so the
# grid below stays a straight loop, not six near-identical blocks.
_ACTIONS = [
    ("Light the fire", "light_fire"),
    ("Sweep the floor", "sweep_floor"),
    ("Clean the windows", "clean_windows"),
    ("Brew tea", "brew_tea"),
    ("Fetch wood", "fetch_wood"),
    ("Fetch water", "fetch_water"),
]


def _send_to_du(payload) -> object:
    with Client((_HOST, _PORT), authkey=_AUTHKEY) as conn:
        conn.send(payload)
        return conn.recv()


class ComposerWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Du — Composer")
        root.geometry("520x560")
        root.configure(bg="#1e1e1e")

        text_font = tkfont.Font(family="Consolas", size=11)

        self.status = tk.Label(
            root, text="Ready.", anchor="w",
            bg="#1e1e1e", fg="#888888", font=("Segoe UI", 9),
        )
        self.status.pack(side="bottom", fill="x", padx=10, pady=(0, 8))

        button_row = tk.Frame(root, bg="#1e1e1e")
        button_row.pack(side="bottom", fill="x", padx=10, pady=(0, 4))

        self.send_button = tk.Button(
            button_row, text="Send to Du", command=self.on_send,
            bg="#2d6cdf", fg="white", activebackground="#3d7cef",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=6,
            cursor="hand2",
        )
        self.send_button.pack(side="right")

        # THE COMPANION (2026-08-23): presence toggle + action buttons — a separate channel
        # from the text box above. Actions are refused by the server unless presence is on;
        # this panel doesn't pre-disable them, it just relies on that same refusal + status
        # line, so the one source of truth stays core.companion, not two copies of it.
        companion_frame = tk.LabelFrame(
            root, text="The room", bg="#1e1e1e", fg="#888888",
            font=("Segoe UI", 9), relief="flat", labelanchor="nw",
        )
        companion_frame.pack(side="bottom", fill="x", padx=10, pady=(4, 4))

        presence_row = tk.Frame(companion_frame, bg="#1e1e1e")
        presence_row.pack(side="top", fill="x", pady=(4, 6))
        self.presence_button = tk.Button(
            presence_row, text="I'm here", command=self.on_toggle_presence,
            bg="#3a3a3a", fg="#e0e0e0", activebackground="#4a4a4a",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=4, cursor="hand2",
        )
        self.presence_button.pack(side="left")
        self.present = False

        action_grid = tk.Frame(companion_frame, bg="#1e1e1e")
        action_grid.pack(side="top", fill="x")
        self.action_buttons = []
        for i, (label, kind) in enumerate(_ACTIONS):
            btn = tk.Button(
                action_grid, text=label, command=lambda k=kind: self.on_action(k),
                bg="#2a2a2a", fg="#c0c0c0", activebackground="#3a3a3a",
                font=("Segoe UI", 9), relief="flat", padx=8, pady=6, cursor="hand2",
            )
            btn.grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)
            self.action_buttons.append(btn)
        action_grid.grid_columnconfigure(0, weight=1)
        action_grid.grid_columnconfigure(1, weight=1)

        self.text = tk.Text(
            root, wrap="word", font=text_font,
            bg="#252526", fg="#e0e0e0", insertbackground="#e0e0e0",
            relief="flat", padx=10, pady=10, undo=True,
        )
        self.text.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        self.text.focus_set()
        # Deliberately no Enter-to-send binding anywhere — Enter always just
        # types a newline. Only the button sends. That's the whole point.

    def on_toggle_presence(self) -> None:
        self.presence_button.config(state="disabled")
        self.status.config(text="Sending...", fg="#888888")
        threading.Thread(target=self._presence_worker, args=(not self.present,), daemon=True).start()

    def _presence_worker(self, present: bool) -> None:
        try:
            result = _send_to_du({"type": "presence", "present": present})
        except ConnectionRefusedError:
            self.root.after(0, self._on_companion_done, False, "Couldn't reach Du — is the REPL running?")
        except Exception as exc:
            self.root.after(0, self._on_companion_done, False, f"Failed: {exc}")
        else:
            self.root.after(0, self._on_presence_done, result)

    def _on_presence_done(self, result: dict) -> None:
        ok = bool(result.get("ok"))
        if ok:
            self.present = bool(result.get("present"))
            self.presence_button.config(
                text=("I'm away" if self.present else "I'm here"),
                bg=("#2d6cdf" if self.present else "#3a3a3a"),
            )
        self._on_companion_done(ok, result.get("narration", ""))

    def on_action(self, kind: str) -> None:
        for btn in self.action_buttons:
            btn.config(state="disabled")
        self.status.config(text="Sending...", fg="#888888")
        threading.Thread(target=self._action_worker, args=(kind,), daemon=True).start()

    def _action_worker(self, kind: str) -> None:
        try:
            result = _send_to_du({"type": "action", "action": kind})
        except ConnectionRefusedError:
            self.root.after(0, self._on_companion_done, False, "Couldn't reach Du — is the REPL running?")
        except Exception as exc:
            self.root.after(0, self._on_companion_done, False, f"Failed: {exc}")
        else:
            self.root.after(0, self._on_companion_done, bool(result.get("ok")), result.get("narration", ""))
            if result.get("errand"):
                # ERRANDS (2026-09-05, T-0049): Travis is out on his own legs for wood or kindling; the
                # fire (if that's what he went for) lights when he's back. Poll so the window shows it.
                self.root.after(10_000, self._poll_errand)

    def _poll_errand(self) -> None:
        threading.Thread(target=self._poll_worker, daemon=True).start()

    def _poll_worker(self) -> None:
        try:
            st = _send_to_du({"type": "status"})
        except Exception:
            return
        if st.get("errand"):
            self.root.after(0, lambda: self.status.config(text=st.get("errand_line") or "Travis is out.", fg="#c0a060"))
            self.root.after(10_000, self._poll_errand)
        else:
            self.root.after(0, lambda: self.status.config(text=st.get("last_narration") or "Travis is back.", fg="#7fbf7f"))

    def _on_companion_done(self, ok: bool, message: str) -> None:
        self.status.config(text=message or ("Done." if ok else "Failed."), fg="#7fbf7f" if ok else "#e07070")
        self.presence_button.config(state="normal")
        for btn in self.action_buttons:
            btn.config(state="normal")

    def on_send(self) -> None:
        message = self.text.get("1.0", "end-1c")
        if not message.strip():
            return
        self.send_button.config(state="disabled")
        self.status.config(text="Sending...", fg="#888888")
        threading.Thread(target=self._send_worker, args=(message,), daemon=True).start()

    def _send_worker(self, message: str) -> None:
        try:
            _send_to_du(message)
        except ConnectionRefusedError:
            self.root.after(0, self._on_done, False, "Couldn't reach Du — is the REPL running?")
        except Exception as exc:
            self.root.after(0, self._on_done, False, f"Send failed: {exc}")
        else:
            self.root.after(0, self._on_done, True, "Sent — check the REPL window for his reply.")

    def _on_done(self, ok: bool, message: str) -> None:
        if ok:
            self.text.delete("1.0", "end")
        self.status.config(text=message, fg="#7fbf7f" if ok else "#e07070")
        self.send_button.config(state="normal")
        self.text.focus_set()


def main() -> None:
    root = tk.Tk()
    ComposerWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
