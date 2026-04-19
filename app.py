import streamlit as st
from groq import Groq
import os, requests, datetime, pandas as pd, re

# --- VIP ELITE KNOWLEDGE BASE ---
VOLT_KNOWLEDGE = """
Role: Senior Tesla Energy Consultant for Volt Home Florida.
Tone: Elite, Minimalist, Professional. 
Rules:
1. NEVER write long paragraphs. Max 2-3 punchy sentences.
2. Use bullet points for value.
3. If data (address/bill) is provided, acknowledge it briefly and push for the phone/email.
4. Once contact info is provided, say: 'Elite choice. Your Tesla ROI report is generating below. I've notified our senior specialist.'
"""

st.set_page_config(page_title="Volt Home | Elite AI", page_icon="⚡", layout="wide")
PRIMARY_COLOR = "#D81B60"

st.markdown(f"""
    <style>
    .stApp {{ background: #050505; }}
    .stButton>button {{ border-radius: 5px; background: {PRIMARY_COLOR}; color: white; font-weight: bold; height: 3.5em; }}
    .stChatMessage {{ border-radius: 10px; border-left: 5px solid {PRIMARY_COLOR}; background: #111; }}
    [data-testid="stMetricValue"] {{ color: {PRIMARY_COLOR} !important; }}
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "lead_data" not in st.session_state: st.session_state.lead_data = {"service": "Solar", "bill": 0, "address": "Not Provided", "contact": None}
if "lead_synced" not in st.session_state: st.session_state.lead_synced = False

# --- LOGIC ---
def trigger_ai_response(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": VOLT_KNOWLEDGE}] + st.session_state.messages)
    ans = res.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": ans})

st.title("⚡ Volt Home | Elite")
st.write("Tesla-Certified Energy Independence.")

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("☀️ Solar"): trigger_ai_response("I want the Tesla Solar experience.")
with c2:
    if st.button("🏠 Roofing"): trigger_ai_response("I need elite Florida roofing.")
with c3:
    if st.button("🔋 Powerwall"): trigger_ai_response("I want 100% independence with Powerwall.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Verify address or share bill..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # Smart Extraction
    if any(word in prompt.lower() for word in ["st", "ave", "miami", "fl", "rd"]): st.session_state.lead_data["address"] = prompt
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match: st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    is_contact = "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split())
    if is_contact and not st.session_state.lead_synced:
        st.session_state.lead_data["contact"] = prompt
        chat_summary = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        try:
            # PURE DATA FOR n8n (No .body.)
            payload = {
                "Client": "Volt Home",
                "chat_log": chat_summary,
                "address": st.session_state.lead_data["address"],
                "contact": st.session_state.lead_data["contact"],
                "bill": st.session_state.lead_data["bill"],
                "service": st.session_state.lead_data["service"]
            }
            requests.post("https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads", json=payload, timeout=10)
            st.toast("🚀 Elite Report Unlocked!")
            st.session_state.lead_synced = True
        except: pass

    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": VOLT_KNOWLEDGE}] + st.session_state.messages)
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

# --- VIP ROI DISPLAY ---
if st.session_state.lead_synced and st.session_state.lead_data["bill"] > 0:
    st.divider()
    st.balloons()
    bill = st.session_state.lead_data["bill"]
    kw = round((bill / 0.15 * 12) / 1450, 1)
    st.success(f"✅ VIP ROI Report: {st.session_state.lead_data['address']}")
    m1, m2, m3 = st.columns(3)
    m1.metric("System Size", f"{kw} kW")
    m2.metric("Tesla Status", "Certified")
    m3.metric("25-Yr Savings", f"${round(bill * 12 * 25 * 0.75, -2):,}")
    st.area_chart(pd.DataFrame({'Year': range(1, 26), 'Savings': [ (bill*12*0.75)*i for i in range(1, 26)]}), x='Year', y='Savings', color=PRIMARY_COLOR)
