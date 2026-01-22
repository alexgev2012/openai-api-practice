import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
from prompts import (
    SYSTEM_PROMPT_SARANYA, SYSTEM_PROMPT_NAREK, SYSTEM_PROMPT_IRINA, 
    SYSTEM_PROMPT_ALEKS, SYSTEM_PROMPT_MILENA, SYSTEM_PROMPT_HASMIK
)

load_dotenv()

client = OpenAI()
# Initialize Supabase
sb_url = os.environ.get("FIRST_SUPABASE_URL")
sb_key = os.environ.get("FIRST_SUPABASE_SERVICE_ROLE_KEY")
sam_brain = create_client(sb_url, sb_key)

def run_agent(user_message, persona_dict, current_theme):
    # This combines the persona with the current round's goal
    system_instruction = (
        f"{persona_dict['content']}\n\n"
        f"CURRENT CONVERSATION THEME: {current_theme}\n"
        "Be natural, avoid repeating yourself, and respond to the last person."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message},
            ],
            temperature=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Wait, what? (Error: {e})"

def simulation():
    # Defined themes for your 3 rounds
    themes = [
        "ROUND 1: Focus on Saranyasoft. Discuss the company's massive success and how Saranya became a billionaire.",
        "ROUND 2: Focus on the Year 2036. Discuss future tech, where your lives are now, and the changing world.",
        "ROUND 3: Focus on Nostalgia. Remember the 2026 TUMO workshop, funny jokes, and how you all met."
    ]

    # Student list
    students = [
        ("Narek", SYSTEM_PROMPT_NAREK),
        ("Irina", SYSTEM_PROMPT_IRINA),
        ("Aleks", SYSTEM_PROMPT_ALEKS),
        ("Milena", SYSTEM_PROMPT_MILENA),
        ("Hasmik", SYSTEM_PROMPT_HASMIK)
    ]

    last_message = "Miss Saranya! We missed you! We were just talking about how much has changed since the workshop."
    
    for round_idx in range(3):
        theme = themes[round_idx]
        print(f"\n{'='*30}\n{theme}\n{'='*30}\n")
        
        # We loop through students in pairs
        for i in range(0, len(students), 2):
            # 1. First Student Speaks
            name1, prompt1 = students[i]
            last_message = run_agent(last_message, prompt1, theme)
            print(f"{name1.upper()}: {last_message}\n")
            
            # 2. Second Student Speaks (if there is one left in the list)
            if i + 1 < len(students):
                name2, prompt2 = students[i+1]
                last_message = run_agent(last_message, prompt2, theme)
                print(f"{name2.upper()}: {last_message}\n")
            
            # 3. Saranya speaks after every two students
            last_message = run_agent(last_message, SYSTEM_PROMPT_SARANYA, theme)
            print(f"SARANYA: {last_message}\n")

if __name__ == "__main__":
    simulation()