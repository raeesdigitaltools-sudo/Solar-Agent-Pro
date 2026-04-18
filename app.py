import streamlit as st
from groq import Groq
import os, requests, datetime, pandas as pd, re

# ---------------------------------------------------------
# 1. VOLT HOME "BRAIN" - WEBSITE DATA & POLICIES
# ---------------------------------------------------------
VOLT_KNOWLEDGE = """
About Volt Home: High-quality Solar, Roofing, and Home Improvement in Florida. 
Tagline: Integrity built-in. Quality you can see.
Key Certification: Tesla Energy Certified Installer.
Core Policies:
- 25-Year Manufacturer Warranty on all panels.
- Lifetime System Installation Guarantee.
- Financing: $0 down options available for qualified homeowners.
- Location: Serving all of Florida (Miami, Tampa, Orlando, etc.).
- Pricing: Depends on roof condition and energy bill, but we offer the most competitive 'Price per Watt' in Florida.
- Roofing: We handle full roof replacements, repairs, and solar-integrated roofing.
- Tesla Powerwall: Expert installation for energy independence during hurricanes.
"""

# ---------------------------------------------------------
# 2. CONFIGURATION & UI
# ---------------------------------------------------------
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"

st.set_page_config(page_title="Volt Home | AI Energy Specialist", page_icon="⚡", layout="wide")

# Theme: Tesla Magenta & Dark Premium
PRIMARY_COLOR = "#D81B60" 
st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(135deg, #1a051d 0%, #000000 100%); }}
    h1, h2, h3, p, span {{ color: #ffffff !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    .stButton>button {{ 
        border-radius: 8px; background: {PRIMARY_COLOR}; color: white; border: none;
        width: 100%; font-weight: bold; height: 3em; transition: 0.3s;
    }}
    .stButton>button:hover {{ border: 1px solid white; box-shadow: 0px 0px 15px {PRIMARY_COLOR}; }}
    [data-testid="stMetricValue"] {{ color: {PRIMARY_COLOR} !important; font-size: 1.8rem; }}
    .chat-bubble {{ padding: 10px; border-radius: 10px; margin-bottom: 10px; }}
    </style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state: st.session_state.messages = []
if "lead_data" not in st.session_state: st.session_state.lead_data = {"service": "Solar", "bill": 0, "address": None, "contact": None}
if "report_unlocked" not in st.session_state: st.session_state.report_unlocked = False

# ---------------------------------------------------------
# 3. INTERFACE
# ---------------------------------------------------------
st.title("⚡ Volt Home | Tesla Certified AI")
st.write("Professional Solar, Roofing & Backup Consultation.")

# Service Selector (Improved Visuals)
st.markdown("### Select Service")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("☀️ Solar Quote"): 
        st.session_state.lead_data["service"] = "Solar"
        st.session_state.messages.append({"role": "user", "content": "I want a new solar quote."})
with c2:
    if st.button("🏠 Roofing"): 
        st.session_state.service_type = "Roofing"
        st.session_state.messages.append({"role": "user", "content": "I'm interested in Roofing/Home Improvement."})
with c3:
    if st.button("🔋 Tesla Powerwall"): 
        st.session_state.service_type = "Battery"
        st.session_state.messages.append({"role": "user", "content": "Tell me about Tesla Powerwall backup."})

# Show Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask about our 25-year warranty or financing..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # Brain Logic: Extract Data Automatically
    # 1. Address Detection (Simple logic)
    if any(word in prompt.lower() for word in ["st", "ave", "road", "fl", "miami", "tampa", "street"]):
        st.session_state.lead_data["address"] = prompt
    
    # 2. Bill Detection
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match:
        st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    # 3. Contact Detection & Sync
    is_contact = "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split())
    if is_contact:
        st.session_state.lead_data["contact"] = prompt
        st.session_state.report_unlocked = True
        # Push to n8n
        try:
            requests.post(N8N_WEBHOOK_URL, json={
                "Client": "Volt Home",
                "Timestamp": str(datetime.datetime.now()),
                **st.session_state.lead_data
            })
            st.toast("🚀 Expert Alert! Your data is synced with our Tesla Specialists.")
        except: pass

    # AI Response (Using the Knowledge Base)
    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        sys_msg = f"""
        Identity: Senior AI Consultant at Volt Home Florida.
        Knowledge Base: {VOLT_KNOWLEDGE}
        
        Strict Rules:
        1. Always answer BASED ONLY on the knowledge provided above. 
        2. If asked about warranty, mention the 25-year Manufacturer warranty and Lifetime Install guarantee.
        3. If asked about financing, mention the $0 down options.
        4. If you don't have the Address or Bill, ask for it politely. 
        5. If you have Address and Bill but NO Contact Info, say: 'I have your custom ROI report ready. Please share your email or phone so I can send the official Tesla-certified quote.'
        6. Tone: Elite, helpful, and closing-oriented.
        """
        
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

# ---------------------------------------------------------
# 4. ROI REPORT (ONLY WHEN DATA IS COMPLETE)
# ---------------------------------------------------------
if st.session_state.report_unlocked and st.session_state.lead_data["bill"] > 0:
    st.divider()
    st.balloons()
    bill = st.session_state.lead_data["bill"]
    # Quick Math
    kw = round((bill / 0.15 * 12) / 1450, 1)
    savings = round(bill * 12 * 25 * 0.75, -2)
    
    st.success(f"✅ ROI Report Generated for: {st.session_state.lead_data['address']}")
    m1, m2, m3 = st.columns(3)
    m1.metric("System Size", f"{kw} kW")
    m2.metric("Warranty", "25 Years")
    m3.metric("Est. Savings", f"${savings:,}")
    
    df = pd.DataFrame({'Year': range(1, 26), 'Savings': [savings/25 * i for i in range(1, 26)]})
    st.area_chart(df, x='Year', y='Savings', color=PRIMARY_COLOR)
