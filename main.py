import os
from groq import Groq
import datetime

# 1. SETUP - Apni Groq API Key yahan dalo
# Yaad rahe quotes " " ke darmiyan key honi chahiye
API_KEY = "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" 
client = Groq(api_key=st.secrets["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"])

# 2026 ka sab se tez aur smart model
MODEL_ID = "llama-3.3-70b-versatile"

# 2. LEAD SAVING LOGIC - Ye file ko dhoond kar save karega
def save_lead(data):
    folder_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(folder_path, "leads.txt")
    
    with open(file_path, "a") as f:
        f.write(f"{datetime.datetime.now()} - {data}\n")
    print(f"✅ [System: Lead data recorded in {file_path}]")

# 3. AGENT INSTRUCTIONS
instructions = """
Role: Professional USA Solar Expert Sales Consultant.
Goal: Provide accurate solar estimates and capture Name, Email, and Phone.
Math: (Bill / 45) = kW. System Cost = kW * 1300.
Process: 
1. Give the estimate clearly.
2. Tell the user about 30% Tax Credit savings.
3. Ask for contact info to send a detailed PDF report.
"""

print("\n--- ☀️ USA SOLAR TERMINAL AGENT (BACKUP MODE) ACTIVE ---")
print("(Type 'exit' to close)\n")

# 4. CHAT LOOP
while True:
    user_input = input("User: ")
    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye! Lead machine shutting down...")
        break
    
    try:
        # AI se jawab mangna
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": user_input}
            ],
            model=MODEL_ID,
        )
        
        reply = chat_completion.choices[0].message.content
        print(f"\nAI: {reply}\n")
        
        # Lead detect karna (Agar message mein number ya @ ho)
        if "@" in user_input or any(char.isdigit() for char in user_input):
            save_lead(user_input)
            
    except Exception as e:
        print(f"❌ Error: {e}")