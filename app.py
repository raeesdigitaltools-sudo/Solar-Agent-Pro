import streamlit as st
from groq import Groq
import os
import requests
import datetime
import pandas as pd
import re
from streamlit_searchbox import st_searchbox

# ---------------------------------------------------------
# 0. CONFIGURATION & VOLT HOME SETTINGS
# ---------------------------------------------------------
# Apna n8n URL yahan check kar lein
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"
GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY" 

# Florida Solar Math
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
# 1. UI & VOLT HOME BRANDING (CSS)
# ---------------------------------------------------------
st.set_page_config(page_title="Volt Home | Energy AI", page_icon="⚡", layout="wide")

if "messages" not in st.session_state: st.session_state.messages = []
if "contact_provided" not in st.session_state: st.session_state.contact_provided = False
if "user_bill" not in st.session_state: st.session_state.user_bill = 200
if "service_type" not in st.session_state: st.session_state.service_type = "Solar"

# Volt Home Theme: Dark Purple & Magenta
PRIMARY_COLOR = "#D81B60" 
BG_GRADIENT = "linear-gradient(135deg, #2D0B31 0%, #000000 100%)"

st.markdown(f"""
    <style>
    .stApp {{ background: {BG_GRADIENT}; }}
    h1, h2, h3, h4, p, span, label {{ color: #ffffff !important; }}
    .stButton>button {{ 
        border-radius: 20px; 
        background-color: {PRIMARY_COLOR}; 
        color: white; 
        border: none;
        padding: 10px 24px;
        font-weight: 700;
        transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: scale(1.05); box-shadow: 0px 5px 15px rgba(216,27,96,0.4); border: 1px solid white; }}
    [data-testid="stMetricValue"] {{ color: {PRIMARY_COLOR} !important; }}
    .stChatFloatingInputContainer {{ background-color: rgba(0,0,0,0.5); }}
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Volt Home AI Specialist")
st.subheader("Tesla Certified Energy Consultation.")

# Address Bar
st.markdown("#### 📍 Step 1: Verify Your Florida Address")
selected_addr = st_searchbox(search_address, key="addr_search", placeholder="Verify your property location...")
if selected_addr: st.success(f"Targeting Property: {selected_addr}")

st.divider()

# Quick Actions (Volt Home Services)
st.markdown(f"#### 🛠️ Step 2: Select Service (Current: **{st.session_state.service_type}**)")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("☀️ Solar Quote"): 
        st.session_state.service_type = "Solar"
        st.session_state.messages.append({"role": "user", "content": "I want a new solar quote."})
with col2:
    if st.button("🏠 Roofing"): 
        st.session_state.service_type = "Roofing"
        st.session_state.messages.append({"role": "user", "content": "I need roofing or home improvement services."})
with col3:
    if st.button("🔋 Tesla Powerwall"): 
        st.session_state.service_type = "Battery"
        st.session_state.messages.append({"role": "user", "content": "I'm interested in a Tesla Powerwall battery backup."})

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# ---------------------------------------------------------
# 3. LOGIC & PAYLOAD (VOLT HOME BRAIN)
# ---------------------------------------------------------
if prompt := st.chat_input("Ask about Tesla Powerwalls or Solar savings..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # A. Extract Bill Amount
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match:
        st.session_state.user_bill = int(bill_match[0][0] or bill_match[0][1])

    # B. Contact Detection & FULL PAYLOAD
    if "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split()):
        st.session_state.contact_provided = True
        est = calculate_solar_metrics(st.session_state.user_bill)
        
        lead_payload = {
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Client": "Volt Home",
            "Service": st.session_state.service_type,
            "Address": selected_addr if selected_addr else "No Address Provided",
            "Contact_Info": prompt,
            "Monthly_Bill": f"${st.session_state.user_bill}",
            "Notes": "Tesla Certified Lead"
        }
        
        try:
            requests.post(N8N_WEBHOOK_URL, json=lead_payload)
            st.toast("🚀 Lead Synced! A Tesla Certified Specialist will contact you.")
        except:
            st.error("Connection Error.")

    # C. AI Response (Volt Home Custom Prompt)
    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        company_info = "Volt Home is a Tesla Certified Installer in Florida focusing on Solar, Roofing, and Powerwalls. High quality and integrity."
        
        sys_msg = f"""
        Role: Lead Energy Consultant at Volt Home.
        Knowledge: {company_info}
        - You are elite, professional, and witty.
        - ALWAYS ask for Email/Phone before giving the final ROI report.
        - Mention: "Since we are Tesla Certified, we ensure the highest installation quality in Florida."
        - Current Service: {st.session_state.service_type}.
        - Do not show the savings chart/metrics in the chat text until they provide contact info.
        """
        
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # D. THE GATEKEEPER: Results
    if st.session_state.contact_provided and st.session_state.service_type == "Solar":
        final_est = calculate_solar_metrics(st.session_state.user_bill)
        st.divider()
        st.balloons()
        st.success(f"✅ Volt Home ROI Report: ${st.session_state.user_bill} Monthly Bill")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("System Size", f"{final_est['kw_size']} kW")
        m2.metric("Net Cost (After Tax Credit)", f"${final_est['net_cost']:,}")
        m3.metric("25-Year Savings", f"${final_est['savings']:,}")
        
        df = pd.DataFrame({
            'Category': ['Utility (No Solar)', 'Volt Solar Investment'],
            '25-Year Total Cost': [final_est['savings'] + final_est['net_cost'], final_est['net_cost']]
        })
        st.bar_chart(df, x='Category', y='25-Year Total Cost', color=PRIMARY_COLOR)
