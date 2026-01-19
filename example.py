#required libraries
import customtkinter as ctk
from dotenv import load_dotenv
from openai import OpenAI
from tkinter import simpledialog, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import json
import os
import shutil
import uuid
from datetime import datetime
from supabase import create_client

# System prompt
load_dotenv()
client = OpenAI()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a highly skilled and experienced expert in algorithms...\n\n"
        "Above all, your responses should be concise...\n"
        "You can write code very well\n"
        "You use all languages of programming\n"
        "Especially you are expert at Python"
    )
}

# set the chat style
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("💬 AI Chat Bot")
app.geometry("950x780")
app.minsize(850, 700)

CHAT_FILE = "chats.json"
IMAGE_DIR = "chat_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

chats = {}
current_chat_id = None

# embeds

def embed_query(text: str) -> list:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
#search
def semantic_search(query_text: str) -> list:
    emb_q = embed_query(query_text)
    res = sb.rpc("match_chunks", {"query_embedding": emb_q, "match_count": 5}).execute()
    rows = res.data or []
    print("RAG OUTPUT:", rows)
    return rows

#create the name for chat
def make_unique_name(name):
    if name not in chats:
        return name
    i = 2
    while f"{name} ({i})" in chats:
        i += 1
    return f"{name} ({i})"

#Save chat at JSON
def save_chats():
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

#Show the chat from JSON
def load_chats():
    global chats, current_chat_id

    if not os.path.exists(CHAT_FILE):
        chats = {}
        new_chat()
        return

    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()

            if not content:
                raise ValueError("Empty JSON file")

            chats = json.loads(content)

    except (json.JSONDecodeError, ValueError):
        # corrupted or empty file → reset safely
        chats = {}

    if not chats:
        new_chat()
    else:
        refresh_sidebar()
        current_chat_id = next(iter(chats))
        load_chat(current_chat_id)


# Chat GUI
def new_chat():
    global current_chat_id

    name = simpledialog.askstring("New Chat", "Chat name:", parent=app)
    if not name or not name.strip():
        name = f"Chat {len(chats)+1} • {datetime.now().strftime('%H:%M')}"

    name = make_unique_name(name.strip())
    chats[name] = []
    current_chat_id = name

    save_chats()
    refresh_sidebar()
    load_chat(name)

def load_chat(chat_id):
    global current_chat_id
    current_chat_id = chat_id

    for widget in chat_frame.winfo_children():
        widget.destroy()

    for content, sender in chats[chat_id]:
        if sender == "image":
            add_image_message(content)
        else:
            add_text_message(content, sender)

def refresh_sidebar():
    for w in sidebar_chats.winfo_children():
        w.destroy()

    for chat_id in chats:
        btn = ctk.CTkButton(
            sidebar_chats,
            text=chat_id,
            anchor="w",
            fg_color="#1f1f1f",
            hover_color="#2b2b2b",
            command=lambda cid=chat_id: load_chat(cid)
        )
        btn.pack(fill="x", pady=4, padx=5)

# send the answer
def send_prompt(event=None):
    text = user_entry.get().strip()
    if not text or not current_chat_id:
        return

    user_entry.delete(0, "end")
    user_entry.configure(state="disabled")

    add_text_message(text, "user")
    chats[current_chat_id].append((text, "user"))
    save_chats()

    # Perform semantic search to get relevant context
    rag_rows = semantic_search(text)

    context = "\n\n".join(
        f"[Source {i+1} | sim={row.get('similarity'):.3f}]\n{row.get('content', '')}"
        for i, row in enumerate(rag_rows)
    )

    rag_message = {
        "role": "system",
        "content": f"Use the retrieved context below to answer. If it doesn't contain the answer, say so. \n\nRETRIEVED CONTEXT:\n{context if context else '(no matches)'}"
    }

    full_user_message = {
        "role": "user",
        "content": text,
    }

    full_message = [rag_message, full_user_message, SYSTEM_PROMPT]

    typing_label.configure(text="AI is typing...")
    threading.Thread(target=get_ai_response, args=(full_message,), daemon=True).start()

#get the response from API key
def get_ai_response(prompt):
    try:
        response = client.responses.create(
            model="gpt-5-nano",
            input=prompt
        )
        ai_text = response.output_text
    except Exception as e:
        ai_text = f"Error: {e}"

    app.after(0, lambda: finish_ai(ai_text))

#show the AI response
def finish_ai(text):
    typing_label.configure(text="")
    add_text_message(text, "ai")
    chats[current_chat_id].append((text, "ai"))
    save_chats()

    user_entry.configure(state="normal")
    user_entry.focus()

# add message 
def add_text_message(text, sender):
    color = "#1f6aa5" if sender == "user" else "#2a2a2a"
    anchor = "e" if sender == "user" else "w"

    label = ctk.CTkLabel(
        chat_frame,
        text=text,
        wraplength=520,
        fg_color=color,
        corner_radius=15,
        text_color="white",
        justify="left",
        font=("Segoe UI", 13),
        padx=15,
        pady=10
    )
    label.pack(anchor=anchor, pady=6, padx=10)

    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)


def attach_image():
    if not current_chat_id:
        return

    path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
    if not path:
        return

    chat_dir = os.path.join(IMAGE_DIR, current_chat_id)
    os.makedirs(chat_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.png"
    saved_path = os.path.join(chat_dir, filename)
    shutil.copy(path, saved_path)

    add_image_message(saved_path)
    chats[current_chat_id].append((saved_path, "image"))
    save_chats()

#add image function
def add_image_message(image_path):
    img = Image.open(image_path)
    img.thumbnail((320, 320))
    photo = ImageTk.PhotoImage(img)

    frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
    frame.pack(anchor="e", pady=6, padx=10)

    label = ctk.CTkLabel(frame, image=photo, text="", corner_radius=12)
    label.image = photo
    label.pack()

    label.bind("<Button-1>", lambda e, p=image_path: open_image(p))

    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1.0)

#open the image to see it
def open_image(path):
    top = ctk.CTkToplevel(app)
    top.title("Image Preview")

    img = Image.open(path)
    photo = ImageTk.PhotoImage(img)

    lbl = ctk.CTkLabel(top, image=photo, text="")
    lbl.image = photo
    lbl.pack(expand=True)

#create the frame widget
main = ctk.CTkFrame(app)
main.pack(fill="both", expand=True)

# part where the chats are shown and you can add new chats
sidebar = ctk.CTkFrame(main, width=230, corner_radius=0)
sidebar.pack(side="left", fill="y")

ctk.CTkLabel(sidebar, text="💬 Chats", font=("Segoe UI", 18, "bold")).pack(pady=15)

ctk.CTkButton(sidebar, text="+ New Chat", height=40, command=new_chat).pack(fill="x", padx=15, pady=(0, 10))

sidebar_chats = ctk.CTkScrollableFrame(sidebar)
sidebar_chats.pack(fill="both", expand=True, padx=10, pady=10)

# part where the prompt and answers are shown and you can write the prompt
chat_area = ctk.CTkFrame(main)
chat_area.pack(side="right", fill="both", expand=True)

chat_canvas = ctk.CTkCanvas(chat_area, bg="#121212", highlightthickness=0)
scrollbar = ctk.CTkScrollbar(chat_area, command=chat_canvas.yview)
chat_canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
chat_canvas.pack(fill="both", expand=True)

chat_frame = ctk.CTkFrame(chat_canvas, fg_color="#121212")
chat_canvas.create_window((0, 0), window=chat_frame, anchor="nw", width=680)

chat_frame.bind("<Configure>", lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox("all")))

typing_label = ctk.CTkLabel(chat_area, text="", text_color="gray")
typing_label.pack(pady=(5, 0))

# add photo button and send it to API
input_frame = ctk.CTkFrame(chat_area, corner_radius=15)
input_frame.pack(fill="x", padx=15, pady=15)

attach_btn = ctk.CTkButton(input_frame, text="📎", width=45, command=attach_image)
attach_btn.pack(side="right", padx=(0, 10))

send_btn = ctk.CTkButton(input_frame, text="Send", width=100, command=send_prompt)
send_btn.pack(side="right", padx=(0, 10))

user_entry = ctk.CTkEntry(input_frame, placeholder_text="Type a message...", height=50, font=("Segoe UI", 14))
user_entry.pack(side="left", fill="x", expand=True, padx=10)
user_entry.bind("<Return>", send_prompt)

# add mainloop
load_chats()
user_entry.focus()
app.mainloop()
