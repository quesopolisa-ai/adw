import time
import threading
import tkinter as tk
from tkinter import ttk
from pynput.keyboard import Key, Controller

class AutoSellerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Seller Macro")
        self.root.geometry("320x220")
        self.root.resizable(False, False)
        
        self.keyboard = Controller()
        self.macro_running = False

        # Customization Variables
        self.interval_var = tk.DoubleVar(value=5.0) # Default: Sell every 5 seconds

        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Title/Description
        ttk.Label(frame, text="Automatically Types:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Label(frame, text="t  ->  /sell cactus  ->  Enter", foreground="blue", font=("Courier", 10)).grid(row=1, column=0, columnspan=2, pady=5)

        # Repeat Interval Input
        ttk.Label(frame, text="Sell Every (Seconds):").grid(row=2, column=0, sticky=tk.W, pady=10)
        self.interval_spinbox = ttk.Spinbox(frame, from_=0.5, to=300.0, increment=0.5, textvariable=self.interval_var, width=10)
        self.interval_spinbox.grid(row=2, column=1, pady=10, padx=10)

        # Status Label
        self.status_label = ttk.Label(frame, text="Status: Stopped", foreground="red", font=("Helvetica", 10, "bold"))
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)

        # Start / Stop Button
        self.toggle_btn = ttk.Button(frame, text="Start Auto-Sell", command=self.toggle_macro)
        self.toggle_btn.grid(row=4, column=0, columnspan=2, sticky="ew")

    def auto_sell_loop(self):
        """Runs in a separate background thread to continuously type the command."""
        # Give you 3 seconds to click back into your game window after pressing Start
        for i in range(3, 0, -1):
            if not self.macro_running:
                return
            self.root.after(0, self.status_label.config, {"text": f"Starting in {i}...", "foreground": "orange"})
            time.sleep(1)

        self.root.after(0, self.status_label.config, {"text": "Status: Running...", "foreground": "green"})

        while self.macro_running:
            try:
                # 1. Open chat
                self.keyboard.press('t')
                self.keyboard.release('t')
                time.sleep(0.2) # Wait for chat frame to open cleanly

                # 2. Type the command string
                self.keyboard.type('/sell cactus')
                time.sleep(0.1)

                # 3. Hit enter to submit
                self.keyboard.press(Key.enter)
                self.keyboard.release(Key.enter)
                
            except Exception as e:
                print(f"Typing error: {e}")

            # Read the current delay slider value and wait before selling again
            interval = max(0.1, self.interval_var.get())
            
            # Sleep in tiny steps so the Stop button can interrupt it instantly
            steps = int(interval / 0.1)
            for _ in range(steps):
                if not self.macro_running:
                    break
                time.sleep(0.1)

    def toggle_macro(self):
        if not self.macro_running:
            self.macro_running = True
            self.toggle_btn.config(text="Stop Auto-Sell")
            
            # Fire up the loop thread so the window stays active and movable
            threading.Thread(target=self.auto_sell_loop, daemon=True).start()
        else:
            self.macro_running = False
            self.status_label.config(text="Status: Stopped", foreground="red")
            self.toggle_btn.config(text="Start Auto-Sell")

    def on_close(self):
        self.macro_running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoSellerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
