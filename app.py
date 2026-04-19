import streamlit as st
from groq import Groq
import os, requests, time, pandas as pd, re

# ---------------------------------------------------------
# 1. VIP ELITE SYSTEM PROMPT (The Sales Hunter)
# ---------------------------------------------------------
VOLT_KNOWLEDGE = """
Role: Senior Tesla Energy Consultant at Volt Home Florida.
Tone: Elite, Confident, High-Energy.

Strict Rules:
1. NEVER repeat bullet points if already shown.
2. If the user provides an address, say: "Miami property? Excellent choice. I'm already looking at the solar potential there."
3. If they provide an email/phone, say: "Elite. I'm locking in your Tesla ROI dashboard right now. Look below!"
4. Keep responses under 2 sentences. Focus on the dashboard.
"""

# ---------------------------------------------------------
# 2. PREMIUM UI & BRANDING
# ---------------------------------------------------------
st.set_page_config(page_title="Volt Home | Tesla AI", page_icon="⚡", layout="wide")
PRIMARY_COLOR = "#D81B60" 

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
if "last_notified_state" not in st.session_state: st.session_state.last_notified_state = ""
if "lead_synced" not in st.session_state: st.session_state.lead_synced = False

N8N_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"

def get_ai_response(user_input):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": VOLT_KNOWLEDGE}] + st.session_state.messages
    )
    return res.choices[0].message.content

# ---------------------------------------------------------
# 4. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Volt Home | Elite Tesla AI")
st.write("Experience the Future of Florida Energy.")

# Quick Action Buttons
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("☀️ Solar Quote"):
        st.session_state.lead_data["service"] = "Solar"
        st.session_state.messages.append({"role": "user", "content": "I want the Tesla Solar experience."})
        st.rerun()
with c2:
    if st.button("🏠 Elite Roofing"):
        st.session_state.lead_data["service"] = "Roofing"
        st.session_state.messages.append({"role": "user", "content": "I need elite Florida-tough roofing."})
        st.rerun()
with c3:
    if st.button("🔋 Powerwall"):
        st.session_state.lead_data["service"] = "Battery"
        st.session_state.messages.append({"role": "user", "content": "I want 100% independence with Tesla Powerwall."})
        st.rerun()

st.divider()

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# User Input & Smart Logic
if prompt := st.chat_input("Verify address or share energy bill..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # A. EXTRACTION LOGIC
    if any(word in prompt.lower() for word in ["st", "ave", "miami", "fl", "rd", "court", "drive", "florida"]):
        clean_addr = re.sub(r'(\$?\d+)|([\w\.-]+@[\w\.-]+)', '', prompt).strip(', ')
        st.session_state.lead_data["address"] = clean_addr if len(clean_addr) > 5 else prompt
    
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match:
        st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    email_match = re.findall(r'[\w\.-]+@[\w\.-]+', prompt)
    phone_match = re.findall(r'\b\d{10,}\b', prompt)
    
    found_contact = False
    if email_match or phone_match:
        st.session_state.lead_data["contact"] = email_match[0] if email_match else phone_match[0]
        found_contact = True

    # B. WEBHOOK TRIGGER (N8N)
    has_addr_bill = (st.session_state.lead_data["address"] != "Not Provided" and st.session_state.lead_data["bill"] > 0)
    
    if has_addr_bill or found_contact:
        current_state = f"{st.session_state.lead_data['address']}-{st.session_state.lead_data['bill']}-{st.session_state.lead_data['contact']}"
        if st.session_state.last_notified_state != current_state:
            chat_log = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            payload = {
                "Client": "Volt Home",
                "Lead_type": "HOT (Contact Received)" if found_contact else "WARM (Partial Data)",
                "chat_log": chat_log,
                **st.session_state.lead_data
            }
            try:
                requests.post(N8N_URL, json=payload, timeout=5)
                st.session_state.last_notified_state = current_state
                if found_contact: st.session_state.lead_synced = True
            except: pass

    # C. DYNAMIC AI RESPONSE
    with st.chat_message("assistant"):
        if found_contact:
            response = "Excellent. I've locked in your Florida property. Generating your Tesla ROI dashboard right now. Look below! 👇"
        else:
            response = get_ai_response(prompt)
        
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ---------------------------------------------------------
# 5. THE MAGIC: ELITE ROI DASHBOARD
# ---------------------------------------------------------
if st.session_state.lead_synced and st.session_state.lead_data["bill"] > 0:
    st.divider()
    
    # Premium Loading Simulation
    with st.status("🚀 Engineering your Tesla ROI Report...", expanded=True) as status:
        st.write("Scanning roof via satellite...")
        time.sleep(0.8)
        st.write("Calculating Federal Tax Credits ($10,000+ Potential)...")
        time.sleep(0.8)
        st.write("Finalizing 25-year energy independence forecast...")
        status.update(label="✅ Elite Report Ready!", state="complete", expanded=False)
    
    st.balloons()
    bill = st.session_state.lead_data["bill"]
    kw = round((bill / 0.15 * 12) / 1450, 1)
    savings = round(bill * 12 * 25 * 0.75, -2)
    
    st.subheader(f"📊 Tesla ROI Dashboard: {st.session_state.lead_data['address']}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Recommended System", f"{kw} kW")
    m2.metric("Tesla Status", "Certified Install")
    m3.metric("25-Year Savings", f"${savings:,}")
    
    # Financial Growth Chart
    chart_data = pd.DataFrame({
        'Year': range(1, 26),
        'Savings': [ (bill*12*0.75)*i for i in range(1, 26)]
    })
    st.area_chart(chart_data, x='Year', y='Savings', color=PRIMARY_COLOR)
    st.info("💡 A senior Tesla specialist has been notified. They will reach out to finalize your custom design.")
