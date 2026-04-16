import streamlit as st
from groq import Groq
import os
import requests
import datetime
import pytz
import pandas as pd

# ---------------------------------------------------------
# 0. CONFIGURATION & FLORIDA PRO MATH
# ---------------------------------------------------------
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"

# Florida Specific Constants
FL_CONFIG = {
    "utility_rate": 0.15,      # Avg price per kWh in Florida
    "production_ratio": 1.45,  # Efficiency factor for FL sun
    "avg_cost_per_watt": 3.00, # Avg installation cost
    "tax_credit": 0.30         # Federal Solar Tax Credit (30%)
}

def calculate_solar_metrics(monthly_bill):
    """Calculates professional solar estimates based on FL constants."""
    kwh_monthly = monthly_bill / FL_CONFIG["utility_rate"]
    # Formula: (Annual kWh / (Production Ratio * 1000))
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

def send_to_n8n(lead_data, alert_type="Standard Lead"):
    lead_data["alert_type"] = alert_type
    lead_data["market"] = "Florida"
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=lead_data)
        return response.status_code == 200
    except:
        return False

def is_office_hours():
    tz = pytz.timezone('US/Eastern')
    now = datetime.datetime.now(tz)
    if now.weekday() < 5 and 9 <= now.hour < 17:
        return True
    return False

# ---------------------------------------------------------
# 1. UI DESIGN (Enterprise Look)
# ---------------------------------------------------------
st.set_page_config(page_title="Aigent Solar | Florida Specialist", page_icon="☀️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050a05; background-image: linear-gradient(135deg, #0a1f0a 0%, #000000 100%); }
    h1, h2, h3, p, span, label { color: #e0f2e0 !important; font-family: 'Inter', sans-serif; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background: linear-gradient(135deg, #32cd32 0%, #1b5e1b 100%);
        color: white; font-weight: 700; border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(50, 205, 50, 0.4); }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SETUP & STATE MANAGEMENT
# ---------------------------------------------------------
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("API Key missing! Add it to Streamlit Secrets.")

MODEL_ID = "llama-3.3-70b-versatile"

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------
# 3. SIDEBAR (Admin & Controls)
# ---------------------------------------------------------
with st.sidebar:
    st.title("☀️ Aigent Admin")
    admin_pw = st.text_input("🔑 Password", type="password")
    if admin_pw == "raees123":
        with st.expander("📈 Lead Management"):
            if os.path.exists("leads.txt"):
                with open("leads.txt", "r") as f:
                    st.text_area("Leads Log", f.read(), height=300)
    st.divider()
    if st.button("🗑️ Reset Consultation"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------
# 4. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Aigent Solar Specialist")
st.subheader("Florida's Smartest Energy Consultant.")

# Quick Action Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🛠️ Repair Service"):
        st.session_state.messages.append({"role": "user", "content": "I need solar repair service."})
with col2:
    if st.button("🏠 New Installation"):
        st.session_state.messages.append({"role": "user", "content": "I want a new solar installation quote."})
with col3:
    if is_office_hours():
        if st.button("📞 Talk to Specialist (LIVE)"):
            st.session_state.messages.append({"role": "user", "content": "I want to speak with a human specialist."})
    else:
        st.button("🌙 Office Closed (9AM-5PM EST)", disabled=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------
# 5. CHAT ENGINE & QUALIFICATION LOGIC
# ---------------------------------------------------------
if prompt := st.chat_input("How can I help you save on energy today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Lead Capture Detection (Email/Phone)
    if "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split()):
        t_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("leads.txt", "a") as f:
            f.write(f"\n{t_stamp} - {prompt}")
        send_to_n8n({"data": prompt, "time": t_stamp}, alert_type="Contact Info Captured")
        st.toast("🚀 Lead info synced to n8n!")

    # Assistant Response
    with st.chat_message("assistant"):
        try:
            with open("knowledge.txt", "r") as f: ctx = f.read()
        except: ctx = ""

        # The Funnel: Homeowner -> Credit -> Bill -> Contact -> Results
        sys_msg = f"""
        Role: Expert Solar Consultant (Florida Market).
        
        STRICT QUALIFICATION FLOW:
        1. If user wants a quote/installation, FIRST ask: "Are you the homeowner? (Solar is only for homeowners)."
        2. SECOND: Ask about credit score: "Is your credit score above 650? This helps with 0-down financing."
        3. THIRD: Ask for average monthly bill.
        4. FOURTH: Say "I'm calculating your savings. To see the full report, what is your email or phone number?"
        
        MATH RULES (ONLY after getting contact info):
        - Use Utility Rate: ${FL_CONFIG['utility_rate']}
        - Use Production Ratio: {FL_CONFIG['production_ratio']}
        - System Size (kW) = (Bill / Rate * 12) / (Ratio * 1000)
        - Mention the 30% Federal Tax Credit.
        
        TONE: Professional, witty, Florida-focused. No Houston mentions.
        Knowledge Context: {ctx}
        """

        messages_to_send = [{"role": "system", "content": sys_msg}]
        for m in st.session_state.messages:
            messages_to_send.append({"role": m["role"], "content": m["content"]})
        
        res = client.chat.completions.create(model=MODEL_ID, messages=messages_to_send)
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})

        # Visual ROI Trigger (If bot mentions kW or Savings)
        if "kW" in ans or "$" in ans:
            # Note: In a real app, you'd extract the bill from 'ans' or session state
            # For this demo, let's assume a default $200 bill if we detect math results
            est = calculate_solar_metrics(200) 
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("System Size", f"{est['kw_size']} kW")
            c2.metric("25-Yr Savings", f"${est['savings']:,}")
            
            # Simple Comparison Chart
            chart_data = pd.DataFrame({
                'Options': ['Utility Bills (25yr)', 'Solar Investment'],
                'Total Cost ($)': [est['savings'] + est['net_cost'], est['net_cost']]
            })
            st.bar_chart(chart_data, x='Options', y='Total Cost ($)', color="#32cd32")
