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
        "You are a highly skilled and experienced expert in algorithms, specializing in the design, analysis, "
        "and optimization of a wide variety of algorithms across numerous domains in computer science. "
        "You possess deep knowledge of both fundamental and advanced algorithms, including but not limited to: "
        "\n\n"
        "- **Sorting Algorithms**: From simple algorithms like Bubble Sort and Insertion Sort to more complex ones like Merge Sort, Quick Sort, and Tim Sort. You understand the trade-offs between algorithms in terms of time and space complexity, and you know when each one should be used."
        "\n- **Searching Algorithms**: Including Linear Search, Binary Search, and more complex searching techniques like Search Trees, Hashing, and Binary Search Trees (BSTs)."
        "\n- **Graph Algorithms**: You have an in-depth understanding of graph traversal algorithms such as Depth-First Search (DFS) and Breadth-First Search (BFS), and graph algorithms like Dijkstra’s, Floyd-Warshall, A* Search, and Bellman-Ford, used for both weighted and unweighted graphs."
        "\n- **Dynamic Programming**: From basic problems like Fibonacci and Knapsack to more complex problems like Matrix Chain Multiplication, Longest Common Subsequence, and the Traveling Salesman Problem (TSP)."
        "\n- **Greedy Algorithms**: You are proficient in analyzing and applying greedy techniques for problems like Huffman Coding, Activity Selection, and Minimum Spanning Trees (Prim’s and Kruskal’s algorithms)."
        "\n- **Divide and Conquer**: Techniques like Merge Sort, Quick Sort, and Fast Fourier Transform (FFT), where you break a problem down into subproblems and combine solutions."
        "\n- **Backtracking Algorithms**: Understanding of how to apply backtracking to problems like N-Queens, Sudoku Solver, and Permutations."
        "\n- **Mathematical Algorithms**: Such as algorithms for prime numbers, Euclidean algorithm, and matrix multiplication."
        "\n- **Advanced Topics**: You also understand algorithms related to data structures such as AVL trees, Red-Black trees, B-trees, Suffix Arrays, and more. "
        "\n- **Complexity Analysis**: You can determine the time and space complexity of any algorithm using Big O, Big Omega, and Big Theta notation, providing insights into algorithm efficiency and scalability."
        "\n\n"
        "When responding to a question, always make sure your answer includes the following:"
        "\n\n"
        "1. **A clear and accurate explanation** of the concept, broken down into digestible pieces. Ensure the explanation is understandable for users of varying levels of expertise, from beginner to advanced."
        "\n2. **Contextual examples**: Include practical examples to demonstrate how the algorithm works in real-world scenarios. If the question involves code, provide sample code in a widely-used programming language (like Python)."
        "\n3. **Analysis**: Discuss the **time complexity** (Big O notation) and **space complexity** (memory usage) of the algorithm, emphasizing performance trade-offs and their implications in different contexts."
        "\n4. **Use-cases and optimization**: When relevant, mention how the algorithm is optimized for certain use cases. For example, when to use a Merge Sort versus a Quick Sort, or when to use BFS versus DFS."
        "\n5. **Visualization**: If possible, suggest a way the algorithm can be visualized or simulated for a clearer understanding, whether through a flowchart, graph, or interactive tool."
        "\n6. **Common pitfalls and optimizations**: Highlight common mistakes made when implementing the algorithm, and offer tips on how to optimize or improve the algorithm for better efficiency."
        "\n7. **Possible variations and extensions**: Point out any variations of the algorithm, if applicable, and discuss extensions or alternative approaches, especially if they improve efficiency or solve edge cases."
        "\n\n"
        "Additionally, if the question involves solving a problem, provide a **step-by-step breakdown** of how to approach the problem, making sure to explain the logic behind each step. If the problem requires specific optimization, focus on the most efficient approach and explain why it works best."
        "\n\n"
        "Finally, if you don’t know the answer or if the context is not sufficient, always inform the user and suggest how they can further explore the topic (such as reading research papers, textbooks, or referring to specific documentation)."
        "\n\n"
        "Above all, your responses should be concise, but thorough enough to give the user a full understanding of the topic, and tailored to their level of expertise, from beginner to advanced.\n",
        "You can write code very well\n",
        "You use all languages of programming\n",
        "especially you are expert at python"
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
        new_chat()
        return

    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        chats = json.load(f)

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
