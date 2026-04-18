import streamlit as st
from groq import Groq
import os, requests, datetime, pandas as pd, re

# --- VOLT HOME BIBLE ---
VOLT_KNOWLEDGE = "Lead AI Sales Consultant for Volt Home Florida. Tesla Certified, 25-Year Warranty, $0 Down."

st.set_page_config(page_title="Volt Home | AI", page_icon="⚡", layout="wide")

if "messages" not in st.session_state: st.session_state.messages = []
if "lead_data" not in st.session_state: 
    st.session_state.lead_data = {"service": "Solar", "bill": 0, "address": "Not provided", "contact": None}
if "lead_synced" not in st.session_state: st.session_state.lead_synced = False

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

st.title("⚡ Volt Home Elite AI")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("☀️ Solar Quote"): trigger_ai_response("Interested in Tesla Solar.")
with c2:
    if st.button("🏠 Roofing"): trigger_ai_response("Need Florida-tough roofing.")
with c3:
    if st.button("🔋 Powerwall"): trigger_ai_response("Want Tesla Powerwall independence.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Ask about our 25-year warranty..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    if any(word in prompt.lower() for word in ["st", "ave", "miami", "fl"]): st.session_state.lead_data["address"] = prompt
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match: st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    is_contact = "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split())
    
    if is_contact and not st.session_state.lead_synced:
        st.session_state.lead_data["contact"] = prompt
        
        # --- NEW: PURI CHAT KO EK TEXT BLOCK MEIN BADALNA ---
        chat_summary = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        
        try:
            payload = {
                "Client": "Volt Home",
                "Chat_History": chat_summary, # Ye naya field hai
                **st.session_state.lead_data
            }
            resp = requests.post(N8N_URL, json=payload, timeout=10)
            if resp.status_code == 200:
                st.toast("🚀 Lead Details Sent to Owner!")
                st.session_state.lead_synced = True
        except: pass

    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": VOLT_KNOWLEDGE}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
