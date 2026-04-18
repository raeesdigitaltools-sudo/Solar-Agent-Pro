import streamlit as st
from groq import Groq
import os, requests, datetime, pandas as pd, re

# ---------------------------------------------------------
# 1. THE VOLT HOME "BIBLE" - (Condensed for Speed)
# ---------------------------------------------------------
VOLT_KNOWLEDGE = """
You are a Senior Sales Consultant for Volt Home Florida. 
Key Points: Tesla Certified Installer, 25-Year Warranty, $0 Down Financing.
Rules: 
1. BE CONCISE. Never write more than 3 short sentences or use 2-3 bullet points.
2. BE DIRECT. Use high-energy 'Sales' language.
3. ALWAYS ask for the Address, Bill, or Contact info to move forward.
4. If a button is clicked, give a 2-sentence 'Power Pitch' then ask for details.
"""

# ---------------------------------------------------------
# 2. UI & CUSTOM CSS
# ---------------------------------------------------------
st.set_page_config(page_title="Volt Home | AI", page_icon="⚡", layout="wide")
PRIMARY_COLOR = "#D81B60" 

st.markdown(f"""
    <style>
    .stApp {{ background: #000000; }}
    .stButton>button {{ border-radius: 8px; background: {PRIMARY_COLOR}; color: white; font-weight: bold; height: 3em; }}
    .stChatMessage {{ border-radius: 10px; margin-bottom: 5px; border-left: 4px solid {PRIMARY_COLOR}; }}
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "lead_data" not in st.session_state: st.session_state.lead_data = {"service": "Solar", "bill": 0, "address": None, "contact": None}

# ---------------------------------------------------------
# 3. SALES DYNAMICS
# ---------------------------------------------------------
st.title("⚡ Volt Home AI")
st.markdown("### Choose your upgrade:")

c1, c2, c3 = st.columns(3)

def trigger_ai_response(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    # Humne yahan 'Strictly Short' ki instruction di hai
    sys_msg = f"{VOLT_KNOWLEDGE}\n\nSTRICT RULE: Give a 2-sentence punchy response and ask for their address or bill."
    
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
    )
    ans = res.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": ans})

with c1:
    if st.button("☀️ Solar Quote"):
        st.session_state.lead_data["service"] = "Solar"
        trigger_ai_response("Show me why Volt Solar is #1.")

with c2:
    if st.button("🏠 Roofing"):
        st.session_state.lead_data["service"] = "Roofing"
        trigger_ai_response("Need a Florida-tough roof.")

with c3:
    if st.button("🔋 Tesla Powerwall"):
        st.session_state.lead_data["service"] = "Battery"
        trigger_ai_response("I want 100% energy independence.")

st.divider()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Ask about 25-yr warranty..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # Data Extraction
    if any(word in prompt.lower() for word in ["st", "ave", "fl", "miami"]):
        st.session_state.lead_data["address"] = prompt
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match: st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    is_contact = "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split())
    if is_contact:
        st.session_state.lead_data["contact"] = prompt
        try:
            requests.post("https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads", json={
                "Client": "Volt Home", **st.session_state.lead_data
            })
            st.toast("🚀 Lead Sent!")
        except: pass

    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        sys_msg = f"{VOLT_KNOWLEDGE}\n\nSTRICT RULE: Maximum 3 short sentences. No fluff. Get the address or email."
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

# Simplified ROI
if st.session_state.lead_data["contact"] and st.session_state.lead_data["bill"] > 0:
    st.balloons()
    bill = st.session_state.lead_data["bill"]
    kw = round((bill / 0.15 * 12) / 1450, 1)
    st.success(f"✅ Estimate for {st.session_state.lead_data['address']}")
    st.metric("System Size", f"{kw} kW")
    st.write(f"Volt Warranty: 25 Years. $0 Down Financing Active.")
