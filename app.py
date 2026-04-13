import streamlit as st
from groq import Groq
import os

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Aigent Solar Specialist", page_icon="☀️", layout="wide")

# Custom CSS for VIP Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FFD700; color: black; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #262730; color: white; }
    </style>
    """, unsafe_allow_index=True)

# 2. SECRETS & SETUP
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
MODEL_ID = "llama-3.3-70b-versatile"

# Initialize files if they don't exist
for f in ["knowledge.txt", "leads.txt"]:
    if not os.path.exists(f):
        with open(f, "w") as file: file.write("")

# 3. SIDEBAR (ADMIN & SECURE AREA)
with st.sidebar:
    st.title("☀️ Aigent")
    st.divider()
    
    # Admin Access Control
    admin_password = st.text_input("🔑 Admin Password", type="password", help="Enter password to manage agent")
    
    if admin_password == "raees123": # <--- Aap apna password badal sakte hain
        st.success("Admin Mode Active")
        
        with st.expander("📂 Knowledge Manager"):
            uploaded_file = st.file_uploader("Upload Pricing/Info (PDF/TXT)", type=['pdf', 'txt'])
            if uploaded_file:
                # Basic logic to save content to knowledge.txt
                content = uploaded_file.read().decode("utf-8") if uploaded_file.type == "text/plain" else "PDF Content Placeholder"
                with open("knowledge.txt", "a") as f:
                    f.write("\n" + content)
                st.toast("Knowledge Updated!")

        with st.expander("📈 Client Dashboard"):
            if st.button("👁️ View Recent Leads"):
                with open("leads.txt", "r") as f:
                    st.text_area("Customer Leads", f.read(), height=200)
    
    else:
        st.info("Log in as admin to update knowledge or view leads.")

    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# 4. MAIN CHAT LOGIC
st.title("⚡ Aigent Solar Specialist")
st.subheader("How can I assist you today?")

# Initial Buttons for User
col1, col2 = st.columns(2)
with col1:
    if st.button("🛠️ Need Repair or Service"):
        st.session_state.messages = [{"role": "user", "content": "I need repair or service for my solar panels."}]
with col2:
    if st.button("🏠 New System Installation"):
        st.session_state.messages = [{"role": "user", "content": "I want to install a new solar system."}]

# Chat History Management
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. AI RESPONSE ENGINE
if prompt := st.chat_input("Ask about solar..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Simple Lead Detection Logic
    if "@" in prompt or len([s for s in prompt.split() if s.isdigit()]) >= 10:
        with open("leads.txt", "a") as f:
            f.write(f"\nLead: {prompt}")

    with st.chat_message("assistant"):
        # Load Knowledge Context
        with open("knowledge.txt", "r") as f:
            context = f.read()
        
        full_prompt = f"Context: {context}\n\nUser Question: {prompt}\nAnswer as a professional Solar Specialist."
        
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": full_prompt}]
        )
        answer = response.choices[0].message.content
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})