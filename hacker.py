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
        # Main Layout Frame
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
        self.toggle_btn.grid(row=3, column=0, columnspan=2, fill=tk.X)

    def on_click(self, x, y, button, pressed):
        # Listen for physical right clicks only when macro is explicitly turned on
        if self.macro_running and pressed and button == Button.right:
            if self.is_clicking:
                return
            
            self.is_clicking = True
            
            # Read variables safely from the UI configuration
            clicks = self.num_clicks_var.get()
            delay = self.delay_var.get()

            # Execute the rapid click chain
            for _ in range(clicks):
                self.mouse.click(Button.right, 1)
                time.sleep(delay)
                
            self.is_clicking = False

    def toggle_macro(self):
        if not self.macro_running:
            # Start the macro listener
            self.macro_running = True
            self.status_label.config(text="Status: Active & Listening", foreground="green")
            self.toggle_btn.config(text="Stop Macro")
            
            # Run the listener in a separate thread to keep the GUI from freezing
            self.listener = Listener(on_click=self.on_click)
            self.listener.start()
        else:
            # Stop the macro listener
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
