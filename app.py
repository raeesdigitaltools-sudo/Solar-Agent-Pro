import streamlit as st
from groq import Groq
import os, requests, datetime, pandas as pd, re

# ---------------------------------------------------------
# 1. VIP ELITE KNOWLEDGE BASE (Minimalist & Professional)
# ---------------------------------------------------------
VOLT_KNOWLEDGE = """
Role: Senior Tesla Energy Consultant for Volt Home Florida.
Tone: Elite, Minimalist, Professional. 
Strict Rules:
1. NEVER write long paragraphs. Max 2-3 short, punchy sentences.
2. Use bullet points for value (Tesla Certified, 25-Year Warranty, $0 Down).
3. If data (address/bill) is provided, acknowledge it briefly and push for phone/email.
4. Once contact info is provided, say: 'Elite choice. Your Tesla ROI report is generating below. I've notified our senior specialist.'
"""

# ---------------------------------------------------------
# 2. PREMIUM UI & BRANDING
# ---------------------------------------------------------
st.set_page_config(page_title="Volt Home | Elite AI", page_icon="⚡", layout="wide")

PRIMARY_COLOR = "#D81B60" # Volt Magenta

st.markdown(f"""
    <style>
    .stApp {{ background: #050505; }}
    h1, h2, h3, p, span {{ color: white !important; font-family: 'Inter', sans-serif; }}
    .stButton>button {{ 
        border-radius: 5px; background: {PRIMARY_COLOR}; color: white; 
        font-weight: bold; height: 3.5em; width: 100%; border: none; transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0px 5px 15px {PRIMARY_COLOR}88; }}
    .stChatMessage {{ background-color: #111; border-radius: 10px; border-left: 5px solid {PRIMARY_COLOR}; }}
    [data-testid="stMetricValue"] {{ color: {PRIMARY_COLOR} !important; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. SESSION STATE & CONFIG
# ---------------------------------------------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "lead_data" not in st.session_state: 
    st.session_state.lead_data = {"service": "Solar", "bill": 0, "address": "Not Provided", "contact": "Not Provided"}
if "lead_synced" not in st.session_state: st.session_state.lead_synced = False

# Aapka n8n Webhook URL
N8N_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"

def trigger_ai_response(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": VOLT_KNOWLEDGE}] + st.session_state.messages
    )
    ans = res.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": ans})

# ---------------------------------------------------------
# 4. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Volt Home | Elite AI")
st.write("Florida's Premium Tesla-Certified Energy Partner.")

# Quick Action Buttons
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("☀️ Solar Quote"):
        st.session_state.lead_data["service"] = "Solar"
        trigger_ai_response("I want the Tesla Solar experience.")
with c2:
    if st.button("🏠 Elite Roofing"):
        st.session_state.lead_data["service"] = "Roofing"
        trigger_ai_response("I need elite Florida-tough roofing.")
with c3:
    if st.button("🔋 Powerwall"):
        st.session_state.lead_data["service"] = "Battery"
        trigger_ai_response("I want 100% independence with Tesla Powerwall.")

st.divider()

# Chat History Display
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# User Input & Extraction Logic
if prompt := st.chat_input("Verify address or share energy bill..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # A. CLEAN EXTRACTION LOGIC
    # Extract Address (Filters out emails and numbers)
    if any(word in prompt.lower() for word in ["st", "ave", "miami", "fl", "rd", "court", "drive"]):
        clean_addr = re.sub(r'(\$?\d+)|([\w\.-]+@[\w\.-]+)', '', prompt).strip(', ')
        st.session_state.lead_data["address"] = clean_addr if len(clean_addr) > 5 else prompt
    
    # Extract Bill
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match:
        st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    # Extract Contact (Email or Phone)
    email_match = re.findall(r'[\w\.-]+@[\w\.-]+', prompt)
    phone_match = re.findall(r'\b\d{10,}\b', prompt)
    
    is_contact = len(email_match) > 0 or len(phone_match) > 0

    # B. WEBHOOK TRIGGER (OWNER NOTIFICATION)
    if is_contact and not st.session_state.lead_synced:
        st.session_state.lead_data["contact"] = email_match[0] if email_match else phone_match[0]
        
        # Prepare Full Chat History
        chat_summary = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        
        try:
            payload = {
                "Client": "Volt Home",
                "chat_log": chat_summary,
                "address": st.session_state.lead_data["address"],
                "contact": st.session_state.lead_data["contact"],
                "bill": st.session_state.lead_data["bill"],
                "service": st.session_state.lead_data["service"]
            }
            resp = requests.post(N8N_URL, json=payload, timeout=10)
            if resp.status_code == 200:
                st.toast("🚀 Elite ROI Report Generated!")
                st.session_state.lead_synced = True
        except:
            pass

    # C. AI RESPONSE
    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": VOLT_KNOWLEDGE}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

# ---------------------------------------------------------
# 5. DYNAMIC VIP ROI RESULTS
# ---------------------------------------------------------
if st.session_state.lead_synced and st.session_state.lead_data["bill"] > 0:
    st.divider()
    st.balloons()
    bill = st.session_state.lead_data["bill"]
    kw = round((bill / 0.15 * 12) / 1450, 1)
    savings = round(bill * 12 * 25 * 0.75, -2)
    
    st.success(f"✅ VIP ROI Report: {st.session_state.lead_data['address']}")
    m1, m2, m3 = st.columns(3)
    m1.metric("System Size", f"{kw} kW")
    m2.metric("Tesla Status", "Certified")
    m3.metric("25-Yr Savings", f"${savings:,}")
    
    chart_data = pd.DataFrame({'Year': range(1, 26), 'Savings': [ (bill*12*0.75)*i for i in range(1, 26)]})
    st.area_chart(chart_data, x='Year', y='Savings', color=PRIMARY_COLOR)
