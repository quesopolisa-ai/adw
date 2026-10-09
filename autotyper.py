import time
import pyautogui
import tkinter as tk
from tkinter import scrolledtext, messagebox

def start_typing():
    text = text_area.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Warning", "Please paste or type some text first!")
        return

    delay = float(delay_entry.get())
    wpm = float(wpm_entry.get())
    
    # Calculate delay per character based on WPM (assume ~5 characters per word)
    chars_per_min = wpm * 5
    interval = 60.0 / chars_per_min if chars_per_min > 0 else 0.05

    messagebox.showinfo("Ready", f"Click OK, then click inside your target document. Typing will start in {delay} seconds.")
    time.sleep(delay)

    pyautogui.typewrite(text, interval=interval)
    messagebox.println("Done", "Finished typing the text.")

# Build a simple GUI window
root = tk.Tk()
root.title("Auto-Typer Simulator")
root.geometry("500x400")

label_instructions = tk.Label(root, text="Paste your text below:")
label_instructions.pack(pady=5)

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=55, height=12)
text_area.pack(pady=5)

frame_settings = tk.Frame(root)
frame_settings.pack(pady=10)

tk.Label(frame_settings, text="Start Delay (sec):").grid(row=0, column=0, padx=5)
delay_entry = tk.Entry(frame_settings, width=8)
delay_entry.insert(0, "5")
delay_entry.grid(row=0, column=1, padx=5)

tk.Label(frame_settings, text="Speed (WPM):").grid(row=0, column=2, padx=5)
wpm_entry = tk.Entry(frame_settings, width=8)
wpm_entry.insert(0, "60")
wpm_entry.grid(row=0, column=3, padx=5)

btn_start = tk.Button(root, text="Start Auto-Typing", command=start_typing, bg="green", fg="white", font=("Arial", 11, "bold"))
btn_start.pack(pady=10)

root.mainloop()
