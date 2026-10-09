import time
import threading
import tkinter as tk
from tkinter import ttk
from pynput.mouse import Listener, Controller, Button

class ClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Right-Click Macro")
        self.root.geometry("300x200")
        self.root.resizable(False, False)
        
        self.mouse = Controller()
        self.is_clicking = False
        self.macro_running = False
        self.listener = None

        # Customization Variables
        self.num_clicks_var = tk.IntVar(value=3)
        self.delay_var = tk.DoubleVar(value=0.05)

        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Number of Clicks
        ttk.Label(frame, text="Number of Clicks:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.clicks_spinbox = ttk.Spinbox(frame, from_=1, to=100, textvariable=self.num_clicks_var, width=10)
        self.clicks_spinbox.grid(row=0, column=1, pady=5, padx=10)

        # Delay Input
        ttk.Label(frame, text="Delay (Seconds):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.delay_spinbox = ttk.Spinbox(frame, from_=0.01, to=5.0, increment=0.01, textvariable=self.delay_var, width=10)
        self.delay_spinbox.grid(row=1, column=1, pady=5, padx=10)

        # Status Label
        self.status_label = ttk.Label(frame, text="Status: Stopped", foreground="red", font=("Helvetica", 10, "bold"))
        self.status_label.grid(row=2, column=0, columnspan=2, pady=15)

        # Start / Stop Button
        self.toggle_btn = ttk.Button(frame, text="Start Macro", command=self.toggle_macro)
        self.toggle_btn.grid(row=3, column=0, columnspan=2, sticky="ew")

    def run_click_sequence(self, target_x, target_y, clicks, delay):
        """Executes a perfectly stable click loop without fighting physical hand movements."""
        try:
            # Snap once to ensure accuracy right where you clicked
            self.mouse.position = (target_x, target_y)
            
            for _ in range(clicks):
                # Using explicit press and release sequences bypasses driver lag
                self.mouse.press(Button.right)
                self.mouse.release(Button.right)
                time.sleep(delay)
        finally:
            self.is_clicking = False

    def on_click(self, x, y, button, pressed):
        if self.macro_running and pressed and button == Button.right:
            if self.is_clicking:
                return  # Block recursive events
            
            self.is_clicking = True
            clicks = self.num_clicks_var.get()
            delay = self.delay_var.get()

            # Delegate tracking immediately to a background thread
            threading.Thread(
                target=self.run_click_sequence, 
                args=(x, y, clicks, delay), 
                daemon=True
            ).start()

    def toggle_macro(self):
        if not self.macro_running:
            self.macro_running = True
            self.status_label.config(text="Status: Active & Listening", foreground="green")
            self.toggle_btn.config(text="Stop Macro")
            self.listener = Listener(on_click=self.on_click)
            self.listener.start()
        else:
            self.macro_running = False
            self.status_label.config(text="Status: Stopped", foreground="red")
            self.toggle_btn.config(text="Start Macro")
            if self.listener:
                self.listener.stop()

    def on_close(self):
        if self.listener:
            self.listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClickerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
