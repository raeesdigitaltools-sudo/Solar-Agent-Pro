import streamlit as st
from groq import Groq
import os
import requests
import datetime
import pytz
import pandas as pd
from streamlit_searchbox import st_searchbox

# ---------------------------------------------------------
# 0. CONFIGURATION & FLORIDA PRO MATH
# ---------------------------------------------------------
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"
GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_API_KEY_HERE" # <--- Yahan apni key lagayein

FL_CONFIG = {
    "utility_rate": 0.15,
    "production_ratio": 1.45,
    "avg_cost_per_watt": 3.00,
    "tax_credit": 0.30
}

def calculate_solar_metrics(monthly_bill):
    kwh_monthly = monthly_bill / FL_CONFIG["utility_rate"]
    system_size_kw = (kwh_monthly * 12) / (FL_CONFIG["production_ratio"] * 1000)
    system_size_kw = round(system_size_kw, 1)
    gross_cost = system_size_kw * 1000 * FL_CONFIG["avg_cost_per_watt"]
    tax_credit_val = gross_cost * FL_CONFIG["tax_credit"]
    net_cost = gross_cost - tax_credit_val
    savings_25_yrs = monthly_bill * 12 * 25 * 0.70
    return {
        "kw_size": system_size_kw,
        "net_cost": round(net_cost, 2),
        "savings": round(savings_25_yrs, -2),
        "tax_credit": round(tax_credit_val, 2)
    }

def search_address(searchterm: str):
    if not searchterm or len(searchterm) < 3: return []
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={searchterm}&types=address&key={GOOGLE_MAPS_API_KEY}"
    try:
        response = requests.get(url).json()
        return [p["description"] for p in response.get("predictions", [])]
    except: return ["Error fetching addresses"]

def send_to_n8n(lead_data, alert_type="Standard Lead"):
    lead_data["alert_type"] = alert_type
    lead_data["market"] = "Florida"
    try:
        requests.post(N8N_WEBHOOK_URL, json=lead_data)
        return True
    except: return False

# ---------------------------------------------------------
# 1. UI & STATE SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="Aigent Solar | Florida", page_icon="☀️", layout="wide")

if "messages" not in st.session_state: st.session_state.messages = []
if "contact_provided" not in st.session_state: st.session_state.contact_provided = False
if "user_bill" not in st.session_state: st.session_state.user_bill = 200

st.markdown("""
    <style>
    .stApp { background-color: #050a05; background-image: linear-gradient(135deg, #0a1f0a 0%, #000000 100%); }
    h1, h2, h3, p, span, label { color: #e0f2e0 !important; }
    .stButton>button { border-radius: 12px; background: linear-gradient(135deg, #32cd32 0%, #1b5e1b 100%); color: white; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Aigent Solar Specialist")
st.subheader("Florida's Smartest Energy Consultant.")

# Address Autocomplete (High-Tech Feel)
st.markdown("#### 📍 Step 1: Verify Your Roof Location")
selected_addr = st_searchbox(search_address, key="addr_search", placeholder="Start typing your street address (e.g. 123 Miami St)...")
if selected_addr: st.success(f"Targeting Roof: {selected_addr}")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🛠️ Repair Service"): st.session_state.messages.append({"role": "user", "content": "I need solar repair."})
with col2:
    if st.button("🏠 New Installation"): st.session_state.messages.append({"role": "user", "content": "I want a new solar quote."})
with col3:
    if st.button("📞 Talk to Specialist (LIVE)"): st.session_state.messages.append({"role": "user", "content": "Connect me to a specialist."})

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# ---------------------------------------------------------
# 3. LOGIC & GATEKEEPER
# ---------------------------------------------------------
if prompt := st.chat_input("Ask me about solar savings..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # Detect Bill Amount
    import re
    bills = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bills: st.session_state.user_bill = int(bills[0][0] or bills[0][1])

    # Detect Contact Info
    if "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split()):
        st.session_state.contact_provided = True
        send_to_n8n({"data": prompt, "address": selected_addr}, "Lead Captured")
        st.toast("🚀 Contact secured! Analyzing data...")

    # AI Response
    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        sys_msg = f"""
        Role: Florida Solar Expert.
        STRICT RULES:
        - If user wants a Quote or Specialist, you MUST ask for Phone/Email FIRST.
        - Say: "I have your data ready. What's your email or phone so I can lock in these Florida incentives for you?"
        - Do NOT show calculations in text until contact is provided.
        - Only talk about Florida. Use witty tone.
        """
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # THE GATEKEEPER: Show results ONLY if contact provided
    if st.session_state.contact_provided:
        est = calculate_solar_metrics(st.session_state.user_bill)
        st.divider()
        st.balloons()
        st.success(f"✅ Success! Report generated for bill: ${st.session_state.user_bill}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("System Size", f"{est['kw_size']} kW")
        m2.metric("Net Cost", f"${est['net_cost']:,}")
        m3.metric("25-Yr Savings", f"${est['savings']:,}")
        
        df = pd.DataFrame({
            'Category': ['Utility (No Solar)', 'Your Solar Investment'],
            'Total 25-Year Cost': [est['savings'] + est['net_cost'], est['net_cost']]
        })
        st.bar_chart(df, x='Category', y='Total 25-Year Cost', color="#32cd32")
