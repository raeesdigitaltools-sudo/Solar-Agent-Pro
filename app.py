import streamlit as st
from groq import Groq
import datetime
import os
from PyPDF2 import PdfReader

# 1. PAGE CONFIG
st.set_page_config(page_title="Aigent Pro - Solar & Service", page_icon="⚡", layout="wide")

# Custom Styling
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #1A1D24; border-right: 1px solid #FFD700; }
    .stButton>button { background-color: #FFD700; color: #0E1117; border-radius: 8px; font-weight: bold; width: 100%; }
    .suggestion-btn { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# 2. FUNCTIONS
def get_pdf_text(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def save_lead(category, data):
    with open("leads.txt", "a") as f:
        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | [{category}] | {data}\n")

# 3. SIDEBAR (Wapis set kar diya)
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>☀️ Aigent</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # --- KNOWLEDGE MANAGER (Ye wapis aa gaya!) ---
    with st.expander("📂 Knowledge Manager"):
        uploaded_file = st.file_uploader("Update Pricing PDF", type="pdf")
        if uploaded_file:
            text = get_pdf_text(uploaded_file)
            with open("knowledge.txt", "w", encoding="utf-8") as f:
                f.write(text)
            st.success("✅ Knowledge Updated!")

    # --- CLIENT DASHBOARD ---
    st.markdown("### 📈 Client Dashboard")
    if st.button("👁️ View Recent Leads"):
        if os.path.exists("leads.txt"):
            with open("leads.txt", "r") as f:
                for line in f.readlines()[-5:]:
                    st.info(line)
        else:
            st.info("No leads yet.")

    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# 4. LOAD PERMANENT KNOWLEDGE
company_context = ""
if os.path.exists("knowledge.txt"):
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        company_context = f.read()

# 5. GROQ SETUP
client = Groq(api_key=st.secrets["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"]) # Apni key yahan check karna
MODEL_ID = "llama-3.3-70b-versatile"

if "messages" not in st.session_state:
    st.session_state.messages = []

# 6. MAIN UI
st.markdown("<h1 style='color: #FFD700;'>⚡ Aigent Solar Specialist</h1>", unsafe_allow_html=True)

# THE BRAIN: REPAIR VS INSTALL LOGIC
base_instructions = f"""
Role: Professional Solar Sales & Service Manager.
Context: {company_context}

SCENARIO 1: REPAIR/SERVICE
- If user needs repair: Ask for the issue and system age.
- Goal: Offer a $99 inspection. Capture Name/Email/Address.

SCENARIO 2: NEW INSTALLATION
- If user needs new system: Use Bill/45 = kW logic.
- Ask for Roof Dimensions (L x W).
- Goal: Site visit booking. Capture Name/Email/Address.

STRICT RULES:
- Reply in 3 sentences max.
- Use professional American English.
"""

# POP-UP SUGGESTIONS (Welcome Screen)
if not st.session_state.messages:
    st.markdown("### How can I assist you today?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛠️ Need Repair or Service"):
            st.session_state.messages.append({"role": "user", "content": "I need help with solar repairing/service."})
            st.rerun()
    with col2:
        if st.button("🏠 New System Installation"):
            st.session_state.messages.append({"role": "user", "content": "I want to install a new solar system."})
            st.rerun()

# 7. CHAT LOGIC
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about solar..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Lead capture category detection
    category = "General"
    if "repair" in prompt.lower() or "service" in prompt.lower(): category = "REPAIR"
    elif "install" in prompt.lower() or "new" in prompt.lower(): category = "INSTALL"
    
    if "@" in prompt or any(char.isdigit() for char in prompt):
        save_lead(category, prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": base_instructions}] + 
                     [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            model=MODEL_ID,
        )
        full_response = response.choices[0].message.content
        st.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})