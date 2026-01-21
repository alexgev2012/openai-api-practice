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
from prompts import SYSTEM_PROMPT1, SYSTEM_PROMPT2
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
        input=messages,
    )

    return response.output_text

# ---------- Wrappers ----------
def chatbotone(user_message):
    return run_bot(user_message, sam_brain, SYSTEM_PROMPT1)

def chatbottwo(user_message):
    return run_bot(user_message, linda_brain, SYSTEM_PROMPT2)

# ---------- Simulation ----------
def simulation():
    output = "Hi Miss Saranya do you remember us?"

    for _ in range(10):
        output = chatbotone(output)
        print("Miss Saranya SAYS:", output)

        output = chatbottwo(output)
        print("Student group SAYS:", output)

simulation()
