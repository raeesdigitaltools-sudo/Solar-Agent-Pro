import streamlit as st
from groq import Groq
import os, requests, datetime, pandas as pd, re

# ---------------------------------------------------------
# 1. THE VOLT HOME "BIBLE" - (Puri Website ka Nichore)
# ---------------------------------------------------------
VOLT_KNOWLEDGE = """
You are the Senior AI Sales Consultant for Volt Home Florida.
Core Business: Solar, Roofing, Home Improvement, and Tesla Powerwalls.
Branding: 'Integrity built-in. Quality you can see.'

SPECIFIC KNOWLEDGE:
- ROOFING: We don't just 'fix' roofs. We build Florida-tough, hurricane-resistant roofing systems. We offer full replacements and repairs. Key selling point: Lifetime System Installation Guarantee.
- SOLAR: 25-Year Manufacturer Warranty. We use top-tier panels.
- TESLA: We are a 'Tesla Energy Certified Installer'. This is elite. We install Powerwalls for 100% energy independence.
- FINANCING: $0 Down options. Solar pays for itself.
- SERVICE AREA: All of Florida.

SALES PERSONALITY:
- Confident, Elite, Professional, but friendly. 
- Don't wait for questions. LEAD the conversation.
- If they click 'Roofing', talk about Florida weather and our lifetime guarantee immediately.
- If they click 'Solar', talk about Tesla quality and the $0 down financing.
"""

# ---------------------------------------------------------
# 2. UI & CUSTOM CSS (Premium Dark Mode)
# ---------------------------------------------------------
st.set_page_config(page_title="Volt Home AI", page_icon="⚡", layout="wide")
PRIMARY_COLOR = "#D81B60" 

st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(135deg, #120314 0%, #000000 100%); }}
    h1, h2, h3 {{ color: white !important; font-family: 'Helvetica Neue', sans-serif; }}
    .stButton>button {{ 
        border-radius: 10px; background: {PRIMARY_COLOR}; color: white; border: none;
        font-weight: bold; height: 3.5em; transition: 0.5s; font-size: 16px;
    }}
    .stButton>button:hover {{ border: 1px solid white; transform: translateY(-3px); box-shadow: 0px 10px 20px {PRIMARY_COLOR}66; }}
    .stChatMessage {{ background-color: #1a1a1a; border-radius: 15px; border: 1px solid #333; margin-bottom: 10px; }}
    [data-testid="stMetricValue"] {{ color: {PRIMARY_COLOR} !important; }}
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "lead_data" not in st.session_state: st.session_state.lead_data = {"service": "Solar", "bill": 0, "address": None, "contact": None}

# ---------------------------------------------------------
# 3. SALES DYNAMICS (Buttons that TRIGGER the AI)
# ---------------------------------------------------------
st.title("⚡ Volt Home Elite AI")
st.markdown("### How can we upgrade your home today?")

c1, c2, c3 = st.columns(3)

# Logic: Buttons now force a high-quality Assistant response
def trigger_ai_response(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    sys_msg = f"{VOLT_KNOWLEDGE}\n\nCURRENT GOAL: The user just clicked a service button. Give them a high-energy, specific pitch about Volt Home's quality in this area and ask for their address or bill to start the quote."
    
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
    )
    ans = res.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": ans})

with c1:
    if st.button("☀️ Get Solar Quote"):
        st.session_state.lead_data["service"] = "Solar"
        trigger_ai_response("I'm interested in a Solar Quote. Tell me why Volt Home is the best.")

with c2:
    if st.button("🏠 Roofing Services"):
        st.session_state.lead_data["service"] = "Roofing"
        trigger_ai_response("I need roofing help. What makes your Florida roofs special?")

with c3:
    if st.button("🔋 Tesla Powerwall"):
        st.session_state.lead_data["service"] = "Battery"
        trigger_ai_response("Tell me about Tesla Powerwall and energy independence.")

st.divider()

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# User Input Logic
if prompt := st.chat_input("Ask about our 25-year warranty..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # Auto-Extract Data
    if any(word in prompt.lower() for word in ["st", "ave", "road", "fl", "miami", "street"]):
        st.session_state.lead_data["address"] = prompt
    
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match:
        st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    is_contact = "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split())
    if is_contact:
        st.session_state.lead_data["contact"] = prompt
        try:
            requests.post("https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads", json={
                "Client": "Volt Home", "Timestamp": str(datetime.datetime.now()), **st.session_state.lead_data
            })
            st.toast("🚀 ROI Report Sent to Specialist!")
        except: pass

    # AI Response
    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        sys_msg = f"{VOLT_KNOWLEDGE}\n\nINSTRUCTIONS: Answer based on the website info. If they provided an address or bill, acknowledge it and push for the phone/email to finish the Tesla-certified quote."
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

# ROI Display Logic
if st.session_state.lead_data["contact"] and st.session_state.lead_data["bill"] > 0:
    st.balloons()
    bill = st.session_state.lead_data["bill"]
    kw = round((bill / 0.15 * 12) / 1450, 1)
    savings = round(bill * 12 * 25 * 0.75, -2)
    st.success(f"✅ VIP ROI Report generated for {st.session_state.lead_data['address']}")
    m1, m2, m3 = st.columns(3)
    m1.metric("System Size", f"{kw} kW")
    m2.metric("Volt Warranty", "25 Yrs")
    m3.metric("Est. Savings", f"${savings:,}")
