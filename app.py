import streamlit as st
from groq import Groq
import os
import requests
import datetime
import pandas as pd
import re
from streamlit_searchbox import st_searchbox

# ---------------------------------------------------------
# 0. CONFIGURATION & FLORIDA PRO MATH
# ---------------------------------------------------------
# Apne n8n ka URL yahan check kar lein
# Isse update karein
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook-test/solar-aigent-leads"
GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY" # Optional for suggestions

FL_CONFIG = {
    "utility_rate": 0.15,
    "production_ratio": 1.45,
    "avg_cost_per_watt": 3.00,
    "tax_credit": 0.30
}

def calculate_solar_metrics(monthly_bill):
    """Calculates professional solar estimates."""
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
        "savings": round(savings_25_yrs, -2)
    }

def search_address(searchterm: str):
    if not searchterm or len(searchterm) < 3: return []
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={searchterm}&types=address&key={GOOGLE_MAPS_API_KEY}"
    try:
        response = requests.get(url).json()
        return [p["description"] for p in response.get("predictions", [])]
    except: return []

# ---------------------------------------------------------
# 1. UI & SESSION STATE
# ---------------------------------------------------------
st.set_page_config(page_title="Aigent Solar | Florida", page_icon="☀️", layout="wide")

if "messages" not in st.session_state: st.session_state.messages = []
if "contact_provided" not in st.session_state: st.session_state.contact_provided = False
if "user_bill" not in st.session_state: st.session_state.user_bill = 200

st.markdown("""
    <style>
    .stApp { background-color: #050a05; background-image: linear-gradient(135deg, #0a1f0a 0%, #000000 100%); }
    h1, h2, h3, h4, p, span, label { color: #e0f2e0 !important; }
    .stButton>button { border-radius: 12px; background: linear-gradient(135deg, #32cd32 0%, #1b5e1b 100%); color: white; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Aigent Solar Specialist")
st.subheader("Florida's Smartest Energy Consultant.")

# Address Bar
st.markdown("#### 📍 Step 1: Verify Your Roof Location")
selected_addr = st_searchbox(search_address, key="addr_search", placeholder="Start typing your street address...")
if selected_addr: st.success(f"Targeting Roof: {selected_addr}")

st.divider()

# Quick Actions
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🛠️ Repair Service"): st.session_state.messages.append({"role": "user", "content": "I need solar repair."})
with col2:
    if st.button("🏠 New Installation"): st.session_state.messages.append({"role": "user", "content": "I want a new solar quote."})
with col3:
    if st.button("📞 Talk to Specialist"): st.session_state.messages.append({"role": "user", "content": "Connect me to a specialist."})

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# ---------------------------------------------------------
# 3. LOGIC & PAYLOAD (THE BRAIN)
# ---------------------------------------------------------
if prompt := st.chat_input("Ask me about solar savings..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # A. Extract Bill Amount
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match:
        st.session_state.user_bill = int(bill_match[0][0] or bill_match[0][1])

    # B. Contact Detection & FULL PAYLOAD for n8n
    if "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split()):
        st.session_state.contact_provided = True
        
        # Calculate fresh metrics for the lead
        est = calculate_solar_metrics(st.session_state.user_bill)
        
        # YE HAI WOH PAYLOAD JO AAPKI SHEET SE MATCH KAREGA
        lead_payload = {
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Address": selected_addr if selected_addr else "No Address Provided",
            "Contact_Info (Email/Phone)": prompt,
            "Monthly_Bill": f"${st.session_state.user_bill}",
            "Estimated_kW": f"{est['kw_size']} kW"
        }
        
        try:
            requests.post(N8N_WEBHOOK_URL, json=lead_payload)
            st.toast("🚀 ROI Report unlocked & Lead synced to Google Sheets!")
        except:
            st.error("Webhook Error: Could not sync to n8n.")

    # C. AI Response
    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        sys_msg = f"""
        Role: Florida Solar Expert.
        - If user wants Quote/Specialist, you MUST ask for Phone/Email FIRST.
        - Say: "I have your data ready. What's your email or phone number so I can send the report?"
        - Do NOT show calculations in text until contact info is provided.
        - Talk about Florida sun and witty tone.
        """
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # D. THE GATEKEEPER: Results
    if st.session_state.contact_provided:
        final_est = calculate_solar_metrics(st.session_state.user_bill)
        st.divider()
        st.balloons()
        st.success(f"✅ Success! Report generated for bill: ${st.session_state.user_bill}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("System Size", f"{final_est['kw_size']} kW")
        m2.metric("Net Cost", f"${final_est['net_cost']:,}")
        m3.metric("25-Yr Savings", f"${final_est['savings']:,}")
        
        df = pd.DataFrame({
            'Category': ['Utility (No Solar)', 'Solar Investment'],
            'Total 25-Year Cost': [final_est['savings'] + final_est['net_cost'], final_est['net_cost']]
        })
        st.bar_chart(df, x='Category', y='Total 25-Year Cost', color="#32cd32")
