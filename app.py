import streamlit as st
from groq import Groq
import pandas as pd
import requests
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Volt Home | Elite Tesla AI", layout="wide")

# Secrets se API Key uthana
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: white; }
    .stButton>button { background-color: #D81B60; color: white; border-radius: 10px; width: 100%; }
    .chat-bubble { padding: 15px; border-radius: 15px; margin: 10px 0; border: 1px solid #D81B60; }
    </style>
    """, unsafe_allow_value=True)

# --- LOGIC FUNCTIONS ---
def send_to_n8n(data):
    try:
        requests.post(N8N_WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"n8n Error: {e}")

def calculate_roi(bill):
    # $150 default logic agar user ne bill nahi dia
    final_bill = bill if bill > 0 else 150
    savings = final_bill * 12 * 25 # 25 years savings
    return final_bill, savings

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "lead_captured" not in st.session_state:
    st.session_state.lead_captured = {"address": None, "bill": 0, "email": None}

# --- SIDEBAR & HEADER ---
st.title("⚡ Volt Home | Elite Tesla AI")
st.caption("Florida's Premium Energy Solution.")

col1, col2, col3 = st.columns(3)
col1.button("☀️ Solar Quote")
col2.button("🏠 Elite Roofing")
col3.button("🔋 Powerwall")

# --- CHAT INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Verify address or share energy bill..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI Processing
    system_prompt = """You are a Tesla Solar Expert. 
    1. Extract 'address', 'bill' (number only), and 'email'.
    2. If the user doesn't provide a bill, remind them to share it but proceed with a $150 average.
    3. Always be professional and elite. 
    Current State: """ + str(st.session_state.lead_captured)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
    )
    
    ai_msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": ai_msg})
    
    with st.chat_message("assistant"):
        st.markdown(ai_msg)

    # --- EXTRACTION LOGIC (Simplified for Demo) ---
    # Aapka extraction logic yahan check karega variables ko
    if "W Hawthorne Rd" in prompt or "Tampa" in prompt: # Example check
        st.session_state.lead_captured["address"] = "3404 W Hawthorne Rd, Tampa, FL"
    
    if "$" in prompt or "bill" in prompt.lower():
        import re
        nums = re.findall(r'\d+', prompt)
        if nums: st.session_state.lead_captured["bill"] = int(nums[0])
    
    if "@" in prompt:
        st.session_state.lead_captured["email"] = prompt

    # --- VIP AUTOMATION TRIGGER ---
    lead = st.session_state.lead_captured
    
    if lead["address"]:
        # Agar sirf address hai, toh 'Preview ROI' dikhao
        display_bill, total_savings = calculate_roi(lead["bill"])
        
        st.divider()
        st.subheader(f"📊 Your Tesla ROI Dashboard (Based on ${display_bill}/mo)")
        
        # Chart Data
        chart_data = pd.DataFrame({
            'Year': ['Now', 'Year 5', 'Year 10', 'Year 25'],
            'Cost with Utility': [display_bill*12, display_bill*12*5, display_bill*12*10, display_bill*12*25],
            'Cost with Tesla Solar': [0, 5000, 5000, 5000] # Simplified investment
        }).set_index('Year')
        
        st.area_chart(chart_data)
        st.success(f"Estimated 25-Year Savings: **${total_savings:,}**")

        # Balloons sirf tab jab EMAIL mil jaye
        if lead["email"]:
            st.balloons()
            st.toast("Elite Proposal Sent to Email!", icon="📩")
        
        # Data n8n ko bhejna
        payload = {
            "Timestamp": datetime.datetime.now().isoformat(),
            "address": lead["address"],
            "bill": display_bill,
            "contact": lead["email"] if lead["email"] else "Not Provided",
            "Lead_type": "HOT" if lead["email"] and lead["bill"] > 0 else "WARM (Default Bill used)",
            "chat_log": str(st.session_state.messages[-2:])
        }
        send_to_n8n(payload)
