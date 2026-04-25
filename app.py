import streamlit as st
from groq import Groq
import pandas as pd
import requests
import datetime
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Volt Home | Elite Tesla AI", layout="wide")

# Secrets se API Key uthana (Make sure your secrets.toml has GROQ_API_KEY)
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Groq API Key missing! Check your Secrets.")

# n8n Webhook URL
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"

# --- 2. ELITE UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #000000; color: white; }
    .stButton>button { 
        background-color: #D81B60; 
        color: white; 
        border-radius: 10px; 
        border: none;
        height: 3em;
        font-weight: bold;
    }
    .stChatFloatingInputContainer { background-color: #000000; }
    div[data-testid="stExpander"] { border: 1px solid #D81B60; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def send_to_n8n(data):
    try:
        requests.post(N8N_WEBHOOK_URL, json=data, timeout=5)
    except:
        pass # Background process, user ko disturb nahi karega

def calculate_roi(bill_value):
    # Agar bill 0 hai toh Florida average $150 pakar lo
    final_bill = bill_value if bill_value > 0 else 150
    annual_savings = final_bill * 12 * 0.9 # 90% offset
    twenty_five_year_savings = annual_savings * 25
    return final_bill, int(twenty_five_year_savings)

# --- 4. SESSION STATE (Memory) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "lead_captured" not in st.session_state:
    st.session_state.lead_captured = {"address": None, "bill": 0, "email": None}

# --- 5. HEADER ---
st.title("⚡ Volt Home | Elite Tesla AI")
st.markdown("##### Florida's Premium Energy Solution.")

col1, col2, col3 = st.columns(3)
col1.button("☀️ Solar Quote")
col2.button("🏠 Elite Roofing")
col3.button("🔋 Powerwall")
st.divider()

# --- 6. CHAT INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Verify address or share energy bill..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Simple Extraction (Demo ke liye keywords check)
    if any(word in prompt.lower() for word in ["rd", "tampa", "st", "ave", "fl"]):
        st.session_state.lead_captured["address"] = prompt
    
    bill_match = re.findall(r'\d+', prompt)
    if "bill" in prompt.lower() and bill_match:
        st.session_state.lead_captured["bill"] = int(bill_match[0])
    
    if "@" in prompt:
        st.session_state.lead_captured["email"] = prompt

    # AI Response Logic
    system_msg = f"""You are an Elite Tesla Solar Expert in Florida.
    Status: {st.session_state.lead_captured}
    - If address is missing, ask for it professionally.
    - If bill is missing, tell them you'll use the $150 average for now, but ask for theirs.
    - If email is missing, explain it's needed to unlock the full ROI Dashboard."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_msg}] + st.session_state.messages
    )
    
    full_response = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    with st.chat_message("assistant"):
        st.markdown(full_response)

    # --- 7. DYNAMIC ROI DASHBOARD ---
    lead = st.session_state.lead_captured
    if lead["address"]:
        display_bill, total_savings = calculate_roi(lead["bill"])
        
        with st.container():
            st.markdown(f"### 📊 Tesla ROI Forecast for: {lead['address']}")
            
            # Chart Data
            chart_data = pd.DataFrame({
                'Year': ['Now', 'Year 5', 'Year 10', 'Year 20', 'Year 25'],
                'Utility Cost ($)': [display_bill*12, display_bill*12*5, display_bill*12*10, display_bill*12*20, display_bill*12*25],
                'Tesla Solar Cost ($)': [2000, 4000, 4000, 4000, 4000]
            }).set_index('Year')
            
            st.area_chart(chart_data, color=["#D81B60", "#2E7D32"])
            st.metric("Estimated 25-Year Savings", f"${total_savings:,}", delta="Tesla Optimized")

            # Final Automation Trigger
            payload = {
                "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "address": lead["address"],
                "bill": display_bill,
                "contact": lead["email"] if lead["email"] else "PENDING",
                "Lead_type": "HOT" if lead["email"] else "WARM (Partial)",
                "chat_log": prompt
            }
            send_to_n8n(payload)

            if lead["email"]:
                st.balloons()
                st.success("ROI Report locked & sent to your email! 📩")
