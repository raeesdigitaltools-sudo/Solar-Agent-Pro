import streamlit as st
from groq import Groq
import os, requests, datetime, pandas as pd, re

# ---------------------------------------------------------
# 1. THE VOLT HOME BIBLE (Elite Knowledge Base)
# ---------------------------------------------------------
VOLT_KNOWLEDGE = """
You are the Lead AI Sales Consultant for Volt Home Florida. 
Key Assets: Tesla Energy Certified Installer, 25-Year Manufacturer Warranty, $0 Down Financing.
Rules: 
1. BE EXTREMELY CONCISE. Max 2-3 short sentences. 
2. Use professional 'Sales' tone. 
3. Always push to get the Address, Bill, or Email/Phone.
4. Current Service Focus: Solar, Roofing, and Tesla Powerwall.
"""

# ---------------------------------------------------------
# 2. PREMIUM UI & BRANDING (Volt Home Theme)
# ---------------------------------------------------------
st.set_page_config(page_title="Volt Home | AI Specialist", page_icon="⚡", layout="wide")

PRIMARY_COLOR = "#D81B60" # Volt Magenta

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(135deg, #0f0211 0%, #000000 100%); }}
    h1, h2, h3, p, span {{ color: white !important; font-family: 'Inter', sans-serif; }}
    .stButton>button {{ 
        border-radius: 10px; background: {PRIMARY_COLOR}; color: white; 
        font-weight: bold; height: 3.5em; width: 100%; border: none; transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0px 5px 15px {PRIMARY_COLOR}88; }}
    .stChatMessage {{ background-color: #161616; border-radius: 12px; border: 1px solid #222; }}
    [data-testid="stMetricValue"] {{ color: {PRIMARY_COLOR} !important; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. SESSION STATE & DATA LOGIC
# ---------------------------------------------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "lead_data" not in st.session_state: 
    st.session_state.lead_data = {"service": "Solar", "bill": 0, "address": "Not provided", "contact": None}
if "lead_synced" not in st.session_state: st.session_state.lead_synced = False

# Webhook URL (Make sure this is your PRODUCTION URL from n8n)
N8N_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"

def trigger_ai_response(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    sys_msg = f"{VOLT_KNOWLEDGE}\n\nUser just selected a service. Give a punchy 2-sentence welcome and ask for details."
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
    )
    ans = res.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": ans})

# ---------------------------------------------------------
# 4. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Volt Home Elite AI")
st.write("Florida's Premium Tesla-Certified Energy Partner.")

# Service Buttons
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("☀️ Solar Quote"):
        st.session_state.lead_data["service"] = "Solar"
        trigger_ai_response("I'm interested in a Tesla-Certified Solar system.")
with c2:
    if st.button("🏠 Roofing"):
        st.session_state.lead_data["service"] = "Roofing"
        trigger_ai_response("I need a hurricane-tough Florida roof.")
with c3:
    if st.button("🔋 Powerwall"):
        st.session_state.lead_data["service"] = "Battery"
        trigger_ai_response("I want 100% independence with Tesla Powerwall.")

st.divider()

# Chat Display
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# User Input & Lead Logic
if prompt := st.chat_input("Ask about our 25-year warranty..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # A. Data Extraction (Smart Logic)
    if any(word in prompt.lower() for word in ["st", "ave", "road", "miami", "tampa", "orlando", "fl"]):
        st.session_state.lead_data["address"] = prompt
    
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match:
        st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    # B. Contact Detection & Webhook Trigger
    is_contact = "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split())
    
    if is_contact and not st.session_state.lead_synced:
        st.session_state.lead_data["contact"] = prompt
        try:
            # DEBUGGING POST REQUEST
            payload = {
                "Client": "Volt Home",
                "Timestamp": str(datetime.datetime.now()),
                **st.session_state.lead_data
            }
            resp = requests.post(N8N_URL, json=payload, timeout=10)
            
            if resp.status_code == 200:
                st.toast("🚀 ROI Report Sent to Specialist!")
                st.session_state.lead_synced = True
            else:
                st.error(f"n8n Error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Connection Failed: {e}")

    # C. AI Response
    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        sys_msg = f"{VOLT_KNOWLEDGE}\n\nSTRICT RULE: Max 3 short sentences. If you have bill/address but no contact, ask for email/phone now."
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

# ---------------------------------------------------------
# 5. DYNAMIC ROI RESULTS
# ---------------------------------------------------------
if st.session_state.lead_synced and st.session_state.lead_data["bill"] > 0:
    st.divider()
    st.balloons()
    bill = st.session_state.lead_data["bill"]
    kw = round((bill / 0.15 * 12) / 1450, 1)
    savings = round(bill * 12 * 25 * 0.75, -2)
    
    st.success(f"✅ Volt Home ROI Generated for Property")
    m1, m2, m3 = st.columns(3)
    m1.metric("System Size", f"{kw} kW")
    m2.metric("Volt Warranty", "25 Years")
    m3.metric("Est. Savings", f"${savings:,}")
    
    # Simple Chart
    chart_data = pd.DataFrame({'Year': range(1, 26), 'Savings': [savings/25 * i for i in range(1, 26)]})
    st.area_chart(chart_data, x='Year', y='Savings', color=PRIMARY_COLOR)
