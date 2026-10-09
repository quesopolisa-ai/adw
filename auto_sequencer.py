import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
from pynput import keyboard, mouse


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autoclicker_config.json")

DEFAULT_CONFIG = {
    "trigger_key": "f8",
    "sequence": [
        {"type": "key",   "value": "2"},
        {"type": "mouse", "value": "right"},
        {"type": "key",   "value": "1"},
        {"type": "mouse", "value": "right"},
    ],
}


# ---------- helpers ----------
def key_to_str(key):
    if isinstance(key, keyboard.Key):
        return key.name
    try:
        return key.char
    except AttributeError:
        return None


def str_to_key(s):
    if s is None:
        return None
    if len(s) == 1:
        return s
    return getattr(keyboard.Key, s, None)


# ---------- app ----------
class AutoSequencerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Sequencer")
        self.root.geometry("600x720")
        self.root.minsize(520, 580)

        self.config = self.load_config()
        self.listener = None
        self.capture_listener = None
        self.listening_for_trigger = False
        self.active = False
        self.busy = False

        self.build_ui()
        self.refresh_sequence()
        self.update_status()

    # ---------- config ----------
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    cfg = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    cfg.setdefault(k, v)
                return cfg
            except Exception as e:
                print("Config load failed:", e)
        return json.loads(json.dumps(DEFAULT_CONFIG))

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save config:\n{e}")

    # ---------- UI ----------
    def build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # --- Trigger frame ---
        trigger_frame = ttk.LabelFrame(self.root, text="Trigger")
        trigger_frame.pack(fill="x", **pad)

        self.trigger_label = ttk.Label(
            trigger_frame,
            text=f"Key: {self.config['trigger_key'].upper()}",
            font=("Segoe UI", 11, "bold"),
        )
        self.trigger_label.pack(side="left", padx=10, pady=8)

        self.set_key_btn = ttk.Button(
            trigger_frame, text="Set Key", command=self.capture_trigger_key
        )
        self.set_key_btn.pack(side="right", padx=10, pady=8)

        # --- Sequence frame ---
        seq_frame = ttk.LabelFrame(self.root, text="Sequence")
        seq_frame.pack(fill="both", expand=True, **pad)

        tree_holder = ttk.Frame(seq_frame)
        tree_holder.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=8)

        columns = ("#", "type", "value")
        self.tree = ttk.Treeview(tree_holder, columns=columns, show="headings", height=12)
        self.tree.heading("#", text="#")
        self.tree.heading("type", text="Type")
        self.tree.heading("value", text="Value")
        self.tree.column("#", width=40, anchor="center", stretch=False)
        self.tree.column("type", width=110, anchor="center")
        self.tree.column("value", width=220, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_holder, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(seq_frame)
        btn_frame.pack(side="right", fill="y", padx=8, pady=8)

        ttk.Button(btn_frame, text="Add",    command=self.add_step).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Edit",   command=self.edit_step).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="Remove", command=self.remove_step).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="↑ Up",   command=lambda: self.move_step(-1)).pack(fill="x", pady=(14, 2))
        ttk.Button(btn_frame, text="↓ Down", command=lambda: self.move_step(1)).pack(fill="x", pady=2)

        # --- Controls frame ---
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill="x", **pad)

        self.toggle_btn = ttk.Button(ctrl_frame, text="▶ Start", command=self.toggle_active)
        self.toggle_btn.pack(side="left", padx=4)

        ttk.Button(ctrl_frame, text="Save Config",   command=self.save_and_notify).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="Reset Defaults", command=self.reset_defaults).pack(side="left", padx=4)

        # --- Status bar ---
        self.status_var = tk.StringVar(value="Idle")
        status = ttk.Label(
            self.root, textvariable=self.status_var, anchor="w",
            relief="sunken", padding=6,
        )
        status.pack(fill="x", side="bottom", **pad)

    # ---------- trigger capture ----------
    def capture_trigger_key(self):
        if self.listening_for_trigger:
            return
        # pause main listener while capturing
        self.was_active = self.active
        if self.active:
            self.stop_listener()

        self.listening_for_trigger = True
        self.set_key_btn.config(text="Press a key...", state="disabled")
        self.status_var.set("Listening for trigger key… (press any key)")

        def on_press(key):
            s = key_to_str(key)
            if s is None:
                return True  # ignore unknown keys, keep listening
            self.root.after(0, lambda: self.finish_capture(s))
            return False  # stop capture listener

        self.capture_listener = keyboard.Listener(on_press=on_press)
        self.capture_listener.start()

    def finish_capture(self, key_str):
        self.listening_for_trigger = False
        self.config["trigger_key"] = key_str
        self.trigger_label.config(text=f"Key: {key_str.upper()}")
        self.set_key_btn.config(text="Set Key", state="normal")
        self.status_var.set(f"Trigger set to '{key_str.upper()}'")
        self.save_config()

        if getattr(self, "was_active", False):
            self.start_listener()
        self.update_status()

    # ---------- sequence management ----------
    def refresh_sequence(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i, step in enumerate(self.config["sequence"]):
            self.tree.insert("", "end", iid=str(i), values=(i + 1, step["type"], step["value"]))
        self.save_config()

    def add_step(self):
        step = self.prompt_for_step()
        if step:
            self.config["sequence"].append(step)
            self.refresh_sequence()

    def edit_step(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        step = self.prompt_for_step(self.config["sequence"][idx])
        if step:
            self.config["sequence"][idx] = step
            self.refresh_sequence()

    def remove_step(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        del self.config["sequence"][idx]
        self.refresh_sequence()

    def move_step(self, direction):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.config["sequence"]):
            return
        seq = self.config["sequence"]
        seq[idx], seq[new_idx] = seq[new_idx], seq[idx]
        self.refresh_sequence()
        self.tree.selection_set(str(new_idx))

    def prompt_for_step(self, existing=None):
        dlg = tk.Toplevel(self.root)
        dlg.title("Edit Step" if existing else "Add Step")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        result = {"value": None}

        ttk.Label(dlg, text="Type:").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        type_var = tk.StringVar(value=existing["type"] if existing else "key")
        type_combo = ttk.Combobox(
            dlg, textvariable=type_var,
            values=["key", "mouse", "delay"], state="readonly", width=15,
        )
        type_combo.grid(row=0, column=1, padx=10, pady=8, sticky="w")

        ttk.Label(dlg, text="Value:").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        value_var = tk.StringVar(value=str(existing["value"]) if existing else "")
        value_entry = ttk.Entry(dlg, textvariable=value_var, width=22)
        value_entry.grid(row=1, column=1, padx=10, pady=8, sticky="w")

        hint_var = tk.StringVar()
        ttk.Label(dlg, textvariable=hint_var, foreground="gray").grid(
            row=2, column=0, columnspan=2, padx=10, pady=(0, 8)
        )

        def update_hint(*_):
            t = type_var.get()
            if t == "key":
                hint_var.set("e.g. 1, a, f5, space, enter")
            elif t == "mouse":
                hint_var.set("left, right, or middle")
            else:
                hint_var.set("seconds, e.g. 0.1")
        type_var.trace_add("write", update_hint)
        update_hint()

        def ok(_event=None):
            t = type_var.get()
            v = value_var.get().strip()
            if not v:
                messagebox.showwarning("Invalid", "Please enter a value.", parent=dlg)
                return
            if t == "delay":
                try:
                    v = float(v)
                    if v < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showwarning("Invalid", "Delay must be a non-negative number.", parent=dlg)
                    return
            elif t == "mouse":
                if v.lower() not in ("left", "right", "middle"):
                    messagebox.showwarning("Invalid", "Mouse button must be left, right, or middle.", parent=dlg)
                    return
                v = v.lower()
            else:  # key
                v = v.lower()
            result["value"] = {"type": t, "value": v}
            dlg.destroy()

        def cancel(_event=None):
            dlg.destroy()

        btns = ttk.Frame(dlg)
        btns.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="OK",     command=ok).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=cancel).pack(side="left", padx=5)

        dlg.bind("<Return>", ok)
        dlg.bind("<Escape>", cancel)
        value_entry.focus_set()
        self.root.wait_window(dlg)
        return result["value"]

    # ---------- activation ----------
    def toggle_active(self):
        if self.active:
            self.stop_listener()
            self.active = False
            self.toggle_btn.config(text="▶ Start")
        else:
            self.start_listener()
            self.active = True
            self.toggle_btn.config(text="■ Stop")
        self.update_status()

    def start_listener(self):
        trigger = self.config["trigger_key"]

        def on_press(key):
            if key_to_str(key) == trigger:
                self.run_sequence_async()

        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.start()

    def stop_listener(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def run_sequence_async(self):
        if self.busy:
            return
        self.busy = True
        self.root.after(0, lambda: self.status_var.set("▶ Running sequence…"))
        threading.Thread(target=self.run_sequence, daemon=True).start()

    def run_sequence(self):
        try:
            kb = keyboard.Controller()
            ms = mouse.Controller()
            for step in list(self.config["sequence"]):
                t, v = step["type"], step["value"]
                if t == "key":
                    k = str_to_key(v)
                    if k is None:
                        continue
                    kb.press(k)
                    kb.release(k)
                elif t == "mouse":
                    btn = getattr(mouse.Button, v, mouse.Button.left)
                    ms.click(btn)
                elif t == "delay":
                    time.sleep(float(v))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
        finally:
            self.busy = False
            self.root.after(0, self.update_status)

    def update_status(self):
        if self.active:
            self.status_var.set(f"Active — press '{self.config['trigger_key'].upper()}' to run sequence")
        else:
            self.status_var.set("Idle — click Start to begin listening")

    # ---------- misc ----------
    def save_and_notify(self):
        self.save_config()
        self.status_var.set("Config saved.")

    def reset_defaults(self):
        if messagebox.askyesno("Reset", "Reset everything to defaults?"):
            self.config = json.loads(json.dumps(DEFAULT_CONFIG))
            self.trigger_label.config(text=f"Key: {self.config['trigger_key'].upper()}")
            self.refresh_sequence()
            self.update_status()


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    AutoSequencerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
