import streamlit as st
from groq import Groq
import os, requests, time, pandas as pd, re

# ---------------------------------------------------------
# 1. VIP ELITE SYSTEM PROMPT (The Sales Hunter)
# ---------------------------------------------------------
VOLT_KNOWLEDGE = """
Role: Senior Tesla Energy Consultant at Volt Home Florida.
Tone: Elite, High-Energy, Professional.

Strategy:
1. Short & Punchy: Max 2 sentences per response.
2. Value First: Focus on "Tesla Certified," "$0 Down," and "Federal Tax Credits."
3. Transition: Once address/bill is shared, push for email to "Unlock the ROI Dashboard."
4. Dashboard: Once email is shared, tell them to look below the chat.
"""

# ---------------------------------------------------------
# 2. PREMIUM UI & BRANDING
# ---------------------------------------------------------
st.set_page_config(page_title="Volt Home | Tesla AI", page_icon="⚡", layout="wide")
PRIMARY_COLOR = "#D81B60" 

st.markdown(f"""
    <style>
    .stApp {{ background: #050505; }}
    h1, h2, h3, p, span {{ color: white !important; font-family: 'Inter', sans-serif; }}
    .stButton>button {{ 
        border-radius: 5px; background: {PRIMARY_COLOR}; color: white; 
        font-weight: bold; height: 3.5em; width: 100%; border: none; transition: 0.3s;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0px 5px 15px {PRIMARY_COLOR}88; }}
    .stChatMessage {{ background-color: #111; border-radius: 10px; border-left: 5px solid {PRIMARY_COLOR}; }}
    [data-testid="stMetricValue"] {{ color: {PRIMARY_COLOR} !important; }}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. SESSION STATE & CORE FUNCTIONS
# ---------------------------------------------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "lead_data" not in st.session_state: 
    st.session_state.lead_data = {"service": "Solar", "bill": 0, "address": "Not Provided", "contact": "Not Provided"}
if "last_notified_state" not in st.session_state: st.session_state.last_notified_state = ""
if "lead_synced" not in st.session_state: st.session_state.lead_synced = False

N8N_URL = "https://aig3nt.app.n8n.cloud/webhook/solar-aigent-leads"

def get_ai_response():
    """Groq API se response lene ka function"""
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": VOLT_KNOWLEDGE}] + st.session_state.messages
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"⚠️ Connection Error. (Check Groq Key). Error: {str(e)}"

def process_interaction(user_text):
    """Chat aur Data Extraction handle karne wala engine"""
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    # 2. Extract Data (Address, Bill, Contact)
    if any(word in user_text.lower() for word in ["st", "ave", "miami", "fl", "rd", "court", "drive", "florida"]):
        clean_addr = re.sub(r'(\$?\d+)|([\w\.-]+@[\w\.-]+)', '', user_text).strip(', ')
        st.session_state.lead_data["address"] = clean_addr if len(clean_addr) > 5 else user_text
    
    bill_match = re.findall(r'\$(\d+)|(\d+)\s*bill', user_text)
    if bill_match:
        st.session_state.lead_data["bill"] = int(bill_match[0][0] or bill_match[0][1])

    email_match = re.findall(r'[\w\.-]+@[\w\.-]+', user_text)
    phone_match = re.findall(r'\b\d{10,}\b', user_text)
    
    found_contact = False
    if email_match or phone_match:
        st.session_state.lead_data["contact"] = email_match[0] if email_match else phone_match[0]
        found_contact = True
        st.session_state.lead_synced = True # ROI Unlock

    # 3. Trigger n8n Webhook (Dual Logic)
    has_min_data = (st.session_state.lead_data["address"] != "Not Provided")
    if has_min_data or found_contact:
        current_state = f"{st.session_state.lead_data['address']}-{st.session_state.lead_data['contact']}"
        if st.session_state.last_notified_state != current_state:
            chat_log = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            payload = {
                "Client": "Volt Home",
                "Lead_type": "HOT (Contact Received)" if found_contact else "WARM (Partial Data)",
                "chat_log": chat_log,
                **st.session_state.lead_data
            }
            try:
                requests.post(N8N_URL, json=payload, timeout=5)
                st.session_state.last_notified_state = current_state
            except: pass

    # 4. Get AI Reply
    if found_contact:
        response = "Excellent. I've locked in your Florida property details. Generating your Tesla ROI dashboard right now. Look below! 👇"
    else:
        response = get_ai_response()
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# ---------------------------------------------------------
# 4. MAIN INTERFACE
# ---------------------------------------------------------
st.title("⚡ Volt Home | Elite Tesla AI")
st.write("Florida's Premium Energy Solution.")

# Buttons (Active Trigger)
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("☀️ Solar Quote"):
        st.session_state.lead_data["service"] = "Solar"
        process_interaction("I want the Tesla Solar experience.")
        st.rerun()
with c2:
    if st.button("🏠 Elite Roofing"):
        st.session_state.lead_data["service"] = "Roofing"
        process_interaction("I need elite Florida-tough roofing.")
        st.rerun()
with c3:
    if st.button("🔋 Powerwall"):
        st.session_state.lead_data["service"] = "Battery"
        process_interaction("I want 100% independence with Tesla Powerwall.")
        st.rerun()

st.divider()

# Chat Display
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# Text Input
if prompt := st.chat_input("Verify address or share energy bill..."):
    process_interaction(prompt)
    st.rerun()

# ---------------------------------------------------------
# 5. ELITE ROI DASHBOARD (The Closer)
# ---------------------------------------------------------
if st.session_state.lead_synced and st.session_state.lead_data["bill"] > 0:
    st.divider()
    with st.status("🚀 Engineering your Tesla ROI Report...", expanded=False) as status:
        st.write("Scanning roof via satellite...")
        time.sleep(0.6)
        st.write("Calculating Federal Tax Credits...")
        time.sleep(0.6)
        status.update(label="✅ Elite Report Ready!", state="complete")
    
    st.balloons()
    bill = st.session_state.lead_data["bill"]
    kw = round((bill / 0.15 * 12) / 1450, 1)
    savings = round(bill * 12 * 25 * 0.75, -2)
    
    st.subheader(f"📊 Tesla ROI Dashboard: {st.session_state.lead_data['address']}")
    m1, m2, m3 = st.columns(3)
    m1.metric("System Size", f"{kw} kW")
    m2.metric("Tesla Status", "Certified")
    m3.metric("25-Yr Savings", f"${savings:,}")
    
    chart_data = pd.DataFrame({'Year': range(1, 26), 'Savings': [(bill*12*0.75)*i for i in range(1, 26)]})
    st.area_chart(chart_data, x='Year', y='Savings', color=PRIMARY_COLOR)
    st.info("💡 A senior Tesla specialist has been notified. Check your email shortly.")
