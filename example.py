import tkinter as tk
from tkinter import Canvas, Frame, Scrollbar
from dotenv import load_dotenv
from openai import OpenAI
import os

# Load environment variables
load_dotenv()
client = OpenAI()

# --- Functions ---
def send_prompt(event=None):
    user_input = user_entry.get().strip()
    if not user_input:
        return

    add_message(user_input, "user")
    user_entry.delete(0, tk.END)

    if user_input.lower() == "exit":
        add_message("Session ended.", "ai")
        return

    try:
        response = client.responses.create(
            model="gpt-5-nano",
            input=user_input
        )
        ai_text = response.output_text
    except Exception as e:
        ai_text = f"Error: {str(e)}"

    add_message(ai_text, "ai")

def add_message(text, sender):
    # Create a frame for the message
    frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
    bubble = tk.Label(
        frame,
        text=text,
        wraplength=400,
        justify=tk.LEFT,
        font=("Helvetica", 12),
        padx=10,
        pady=6,
        bg="#1a73e8" if sender=="user" else "#e5e5ea",
        fg="white" if sender=="user" else "black",
        bd=0,
        relief=tk.FLAT,
    )
    bubble.pack(anchor='e' if sender=="user" else 'w', padx=10, pady=2)
    frame.pack(fill=tk.BOTH, expand=True)

    # Auto-scroll
    canvas.update_idletasks()
    canvas.yview_moveto(1.0)

# --- GUI Setup ---
root = tk.Tk()
root.title("💬 AI Chat Bot")
root.geometry("600x700")
root.configure(bg="#f5f5f5")

# Chat Canvas with Scrollbar
canvas = Canvas(root, bg="#f5f5f5", highlightthickness=0)
scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)

# Scrollable frame inside canvas
scrollable_frame = Frame(canvas, bg="#f5f5f5")
canvas.create_window((0,0), window=scrollable_frame, anchor="nw", width=580)

def configure_scroll(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
scrollable_frame.bind("<Configure>", configure_scroll)

# --- Input Frame ---
input_frame = Frame(root, bg="#f5f5f5")
input_frame.pack(fill=tk.X, padx=10, pady=10)

user_entry = tk.Entry(input_frame, font=("Helvetica", 14))
user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
user_entry.bind("<Return>", send_prompt)

send_button = tk.Button(
    input_frame,
    text="Send",
    command=send_prompt,
    font=("Helvetica", 12, "bold"),
    bg="#1a73e8",
    fg="white",
    activebackground="#0c59d1",
    activeforeground="white",
    padx=20,
    pady=5,
    relief=tk.FLAT
)
send_button.pack(side=tk.RIGHT)

root.mainloop()
