import streamlit as st
from groq import Groq
import os
import requests
import datetime
import pytz 

# ---------------------------------------------------------
# 0. CONFIGURATION (ST.SECRETS USE KIYA HAI)
# ---------------------------------------------------------
# n8n Webhook (Isay aap kal Production URL se badal sakte hain)
N8N_WEBHOOK_URL = "https://aig3nt.app.n8n.cloud/webhook-test/solar-aigent-leads"

def send_to_n8n(lead_data, alert_type="Standard Lead"):
    lead_data["alert_type"] = alert_type
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
# 1. UI DESIGN (VIP GREENERY THEME)
# ---------------------------------------------------------
st.set_page_config(page_title="Aigent Solar | Florida", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    .stApp { 
        background-color: #050a05; 
        background-image: linear-gradient(135deg, #0a1f0a 0%, #000000 100%); 
    }
    h1, h2, h3, p, span, label { color: #e0f2e0 !important; font-family: 'Inter', sans-serif; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background: linear-gradient(135deg, #32cd32 0%, #1b5e1b 100%);
        color: white; font-weight: 700; border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        transform: translateY(-3px); 
        box-shadow: 0 6px 20px rgba(50, 205, 50, 0.4); 
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SETUP (ST.SECRETS SE API KEY UTHAYE GA)
# ---------------------------------------------------------
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("API Key missing! Please add GROQ_API_KEY in Streamlit Secrets.")

MODEL_ID = "llama-3.3-70b-versatile"

# Files check
for f in ["knowledge.txt", "leads.txt"]:
    if not os.path.exists(f):
        with open(f, "w") as file: file.write("")

# ---------------------------------------------------------
# 3. SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.title("☀️ Aigent")
    admin_pw = st.text_input("🔑 Admin Password", type="password")
    if admin_pw == "raees123":
        with st.expander("📈 Leads Dashboard"):
            if st.button("View Recent Leads"):
                with open("leads.txt", "r") as f:
                    st.text_area("Customer Leads", f.read(), height=300)
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------
# 4. MAIN INTERFACE (3 COLUMNS)
# ---------------------------------------------------------
st.title("⚡ Aigent Solar Specialist")
st.subheader("Your Green Energy Journey Starts Here.")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🛠️ Repair Service"):
        st.session_state.messages.append({"role": "user", "content": "[ACTION: REPAIR_SERVICE]"})
with col2:
    if st.button("🏠 New Installation"):
        st.session_state.messages.append({"role": "user", "content": "[ACTION: NEW_INSTALLATION]"})
with col3:
    if is_office_hours():
        if st.button("📞 Talk to Specialist (LIVE)"):
            t_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_to_n8n({"message": "URGENT: Client wants to talk live!", "time": t_stamp}, alert_type="PRIORITY_LIVE")
            st.session_state.messages.append({"role": "user", "content": "I want to speak with a human specialist now."})
            st.toast("🔔 Alerting the team...")
    else:
        st.button("🌙 Office Closed (9AM-5PM EST)", disabled=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat
for msg in st.session_state.messages:
    display_content = msg["content"]
    if "[ACTION: REPAIR_SERVICE]" in display_content: display_content = "🛠️ I'm looking for solar repair services."
    elif "[ACTION: NEW_INSTALLATION]" in display_content: display_content = "🏠 I'm interested in a new solar installation."
    with st.chat_message(msg["role"]):
        st.markdown(display_content)

# ---------------------------------------------------------
# 5. ENGINE
# ---------------------------------------------------------
if prompt := st.chat_input("Ask about solar in Florida..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if "@" in prompt or any(len(s) >= 10 and s.isdigit() for s in prompt.split()):
        t_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("leads.txt", "a") as f:
            f.write(f"\n{t_stamp} - {prompt}")
        send_to_n8n({"data": prompt, "time": t_stamp}, alert_type="New Lead")
        st.toast("🚀 Lead Recorded!")

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        try:
            with open("knowledge.txt", "r") as f: ctx = f.read()
        except: ctx = ""
        
        sys_msg = f"""
        Role: Professional Solar Expert for Florida.
        If user triggered [ACTION: NEW_INSTALLATION]: Greet warmly and ask for average monthly bill.
        If user triggered [ACTION: REPAIR_SERVICE]: Show urgency and ask for issue description.
        Math: Bill/45=kW, Cost=kW*3000, TaxCredit=30%.
        Knowledge: {ctx}
        """
        
        messages_to_send = [{"role": "system", "content": sys_msg}]
        for m in st.session_state.messages:
            messages_to_send.append({"role": m["role"], "content": m["content"]})
        
        res = client.chat.completions.create(model=MODEL_ID, messages=messages_to_send)
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
