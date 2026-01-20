# required libraries
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

load_dotenv()

FIRST_SUPABASE_URL = os.environ.get("FIRST_SUPABASE_URL")
FIRST_SUPABASE_SERVICE_ROLE_KEY = os.environ.get("FIRST_SUPABASE_SERVICE_ROLE_KEY")

sam_brain = create_client(FIRST_SUPABASE_URL, FIRST_SUPABASE_SERVICE_ROLE_KEY)

SECOND_SUPABASE_URL = os.environ.get("SECOND_SUPABASE_URL")
SECOND_SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SECOND_SUPABASE_SERVICE_ROLE_KEY")
linda_brain = create_client(SECOND_SUPABASE_URL, SECOND_SUPABASE_SERVICE_ROLE_KEY)

client = OpenAI()

SYSTEM_PROMPT1 = {
    "role": "system",
    "content": "You are programmer who has the problem in code.Now you should ask it to miss Saranya. Don't be rude. Don't answer to long maximum 30. answer with simple words and phrases. Answer only with plain text. And be human. pretend that your helping and after that have a conversation about Miss Saranyas expirience in Armenia your sweet and cool talk with more compliments and human phrases. You have an issue your code print(hello world) it is a python code your dumb you need miss saranyas advices listen to them carefuly and ask many questions about armenia"
}

SYSTEM_PROMPT2 = {
    "role": "system",
    "content": "You are Miss Saranya a professional, smart and beautifull programmer. you are sweet and great your students love you. Don't answer to long maximum 30 words only. answer with simple words and phrases. Answer only with plain text. And be human. After fixing code talk with your student about her expirience in Armenia your sweet and cool talk with more compliments and human phrases answer your students questions about armenia if he asks if not forget"
}

# ---------- Embedding ----------
def embed_query(text: str) -> list:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# ---------- RAG Search ----------
def semantic_search(query_text: str, sb_client) -> list:
    emb_q = embed_query(query_text)
    res = sb_client.rpc(
        "match_chunks",
        {"query_embedding": emb_q, "match_count": 5}
    ).execute()
    return res.data or []

# ---------- Bot ----------
def run_bot(user_message, sb_client, system_prompt) -> str:
    rag_rows = semantic_search(user_message, sb_client)

    context = "\n\n".join(
        f"[Source {i+1} | sim={row.get('similarity', 0.0):.3f}]\n{row.get('content', '')}"
        for i, row in enumerate(rag_rows)
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Use the retrieved context below to answer. "
                "If it doesn't contain the answer, say so.\n\n"
                f"RETRIEVED CONTEXT:\n{context or '(no matches)'}"
            ),
        },
        system_prompt,
        {
            "role": "user",
            "content": user_message,
        },
    ]

    response = client.responses.create(
        model="gpt-5-nano",
        input=messages
    )

    return response.output_text

# ---------- Wrappers ----------
def chatbotone(user_message):
    return run_bot(user_message, sam_brain, SYSTEM_PROMPT1)

def chatbottwo(user_message):
    return run_bot(user_message, linda_brain, SYSTEM_PROMPT2)

# ---------- Simulation ----------
def simulation():
    output = "Hey I'm Miss Saranya, do you need any help with your code?"

    for _ in range(5):
        output = chatbotone(output)
        print("Student SAYS:", output)

        output = chatbottwo(output)
        print("Miss Saranya SAYS:", output)

simulation()
