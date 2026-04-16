import streamlit as st
from groq import Groq
import os
import requests
import datetime
import pytz
import pandas as pd
import re
from streamlit_searchbox import st_searchbox

# ---------------------------------------------------------
# 0. CONFIGURATION & FLORIDA PRO MATH
# ---------------------------------------------------------
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"
# Note: Google Maps API key is required for address suggestions
GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY_HERE" 

FL_CONFIG = {
    "utility_rate": 0.15,      # Avg price per kWh in Florida
    "production_ratio": 1.45,  # Efficiency factor for FL sun
    "avg_cost_per_watt": 3.00, # Avg installation cost
    "tax_credit": 0.30         # Federal Tax Credit
}

def calculate_solar_metrics(monthly_bill):
    """Calculates professional solar estimates based on FL constants."""
    kwh_monthly = monthly_bill / FL_CONFIG["utility_rate"]
    # Formula: $$ \text{System Size (kW)} = \frac{\text{Monthly Bill} / \text{Rate} \times 12}{\text{Ratio} \times 1000} $$
    system_size_kw = (kwh_monthly * 12) / (FL_CONFIG["production_ratio"] * 1000)
    system_size_kw = round(system_size_kw, 1)
    
    gross_cost = system_size_kw * 1000 * FL_CONFIG["avg_cost_per_watt"]
    tax_credit_val = gross_cost * FL_CONFIG["tax_credit"]
    net_cost = gross_cost - tax_credit_val
    
    # 25-Year Savings Estimate (Approx 70% offset)
    savings_25_yrs = monthly_bill * 12 * 25 * 0.70
    
    return {
        "kw_size": system_size_kw,
        "net_cost": round(net_cost, 2),
        "savings": round(savings_25_yrs, -2),
        "tax_credit": round(tax_credit_val, 2)
    }

def search_address(searchterm: str):
    """Fetches real addresses from Google Maps API."""
    if not searchterm or len(searchterm) < 3:
        return []
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={searchterm}&types=address&key={GOOGLE_MAPS_API_KEY}"
    try:
        response = requests.get(url).json()
        return [p["description"] for p in response.get("predictions", [])]
    except:
        return ["API Key Required for Suggestions"]

def send_to_n8n(lead_payload, alert_type="Standard Lead"):
    """Sends payload to n8n matching the Google Sheet columns."""
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=lead_payload)
        return response.status_code == 200
    except:
        return False

# ---------------------------------------------------------
# 1. UI & SESSION STATE SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="Aigent Solar | Florida Specialist", page_icon="☀️", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "contact_provided" not in st.session_state:
    st.session_state.contact_provided = False
if "user_bill" not in st.session_state:
    st.session_state.user_bill = 200 # Default fallback

st.markdown("""
    <style>
    .stApp { background-color: #050a05; background-image: linear-gradient(135deg, #0a1f0a 0%, #000000 100%); }
    h1, h2, h3, h4, p, span, label { color: #e0f2e0 !important; font-family: 'Inter', sans-serif; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background: linear-gradient(135deg, #32cd32 0%, #1b5e1b 100%);
        color: white; font-weight: 700; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Aigent Solar Specialist")
st.subheader("Florida's Smartest Energy Consultant.")

# STEP 1: Address Autocomplete
st.markdown("#### 📍 Step 1: Verify Your Roof Location")
selected_addr = st_searchbox(
    search_address, 
    key="addr_search", 
    placeholder="Start typing your street address (e.g. 123 Miami St)..."
)
if selected_addr:
    st.success(f"✅ Targeting Roof Orientation: {selected_addr}")

st.divider()

# Action Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🛠️ Repair Service"):
        st.session_state.messages.append({"role": "user", "content": "I need solar repair service."})
with col2:
    if st.button("🏠 New Installation"):
        st.session_state.messages.append({"role": "user", "content": "I want a new solar installation quote."})
with col3:
    if st.button("📞 Talk to Specialist (LIVE)"):
        st.session_state.messages.append({"role": "user", "content": "I want to speak with a human specialist."})

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------
# 3. CHAT ENGINE & GATEKEEPER LOGIC
# ---------------------------------------------------------
if prompt := st.chat_input("How can I help you save on energy today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # A. Extract Bill Amount from chat
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', prompt)
    if bill_match:
        st.session_state.user_bill = int(bill_match[0][0] or bill_match[0][1])

    # B. Detect Contact Info & Trigger n8n
    if "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split()):
        st.session_state.contact_provided = True
        
        # Prepare Payload for Google Sheets
        est = calculate_solar_metrics(st.session_state.user_bill)
        lead_payload = {
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Address": selected_addr if selected_addr else "No Address Provided",
            "Contact_Info": prompt,
            "Monthly_Bill": f"${st.session_state.user_bill}",
            "Estimated_kW": f"{est['kw_size']} kW"
        }
        
        send_to_n8n(lead_payload, "New Lead Captured")
        st.toast("🚀 ROI Report unlocked & Lead synced to Google Sheets!")

    # C. AI Assistant Response
    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        sys_msg = f"""
        Role: Florida Solar Expert.
        CONSTRAINTS:
        - If user wants a Quote/Savings/Specialist, you MUST ask for Phone or Email FIRST.
        - Say: "I have your custom ROI report ready. What's your email or phone number so I can send it over and lock in these incentives?"
        - Do NOT show math/charts until they provide contact info.
        - Tone: Professional, Witty, Florida-proud. No Houston mentions.
        """
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # D. THE GATEKEEPER: Results section
    if st.session_state.contact_provided:
        final_est = calculate_solar_metrics(st.session_state.user_bill)
        st.divider()
        st.balloons()
        st.success(f"✅ Your Custom Solar Assessment for a ${st.session_state.user_bill} Monthly Bill")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Recommended System", f"{final_est['kw_size']} kW")
        m2.metric("Net Investment", f"${final_est['net_cost']:,}")
        m3.metric("Estimated 25-Yr Savings", f"${final_est['savings']:,}", delta="↑ High ROI")
        
        # Comparison Chart
        chart_data = pd.DataFrame({
            'Financial Comparison': ['Utility Bills (25yr - No Solar)', 'Total Solar Investment'],
            'Cost ($)': [final_est['savings'] + final_est['net_cost'], final_est['net_cost']]
        })
        st.markdown("### 📊 Lifetime Savings Potential")
        st.bar_chart(chart_data, x='Financial Comparison', y='Cost ($)', color="#32cd32")
