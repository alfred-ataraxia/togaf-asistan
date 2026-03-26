import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta
import hashlib

# --- CONFIGURATION ---
ST_TITLE = "TOGAF 10 Kurumsal Mimari Asistanı"
ST_ICON = "🏢"
MAX_DAILY_QUOTA_PER_IP = 50  # IP başı günlük limit

# --- PAGE SETUP ---
st.set_page_config(page_title=ST_TITLE, page_icon=ST_ICON, layout="centered")

st.title(f"{ST_ICON} {ST_TITLE}")
st.caption("TOGAF 10 Standartları ve ADM Döngüsü Üzerine Uzmanlaşmış Kurumsal Destek Sistemi")

# --- IP LIMIT & TRACKING ---
def get_client_ip():
    try:
        return st.context.headers.get("X-Forwarded-For", "unknown").split(",")[0].strip()
    except:
        return "unknown"

client_ip = get_client_ip()
ip_hash = hashlib.md5(client_ip.encode()).hexdigest()[:8]

if "ip_usage" not in st.session_state:
    st.session_state.ip_usage = {}

if "usage_reset_date" not in st.session_state:
    st.session_state.usage_reset_date = datetime.now().date()

if st.session_state.usage_reset_date != datetime.now().date():
    st.session_state.ip_usage = {}
    st.session_state.usage_reset_date = datetime.now().date()

current_usage = st.session_state.ip_usage.get(ip_hash, 0)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://www.opengroup.org/sites/default/files/togaf_logo.png", width=150)
    st.divider()
    st.markdown(f"**IP Kodu:** `{ip_hash}`")
    st.markdown(f"**Günlük Limit:** {MAX_DAILY_QUOTA_PER_IP} Sorgu")
    
    remaining = MAX_DAILY_QUOTA_PER_IP - current_usage
    st.progress(remaining / MAX_DAILY_QUOTA_PER_IP, text=f"Kalan: {remaining}/{MAX_DAILY_QUOTA_PER_IP}")
    
    st.divider()
    st.info("Bu asistan resmi TOGAF 10 dökümantasyonu üzerine uzmanlaşmıştır.")

# --- API SETUP ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("API anahtarı bulunamadı.")
    st.stop()

# --- MODEL SETUP ---
AVAILABLE_MODELS = [
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
    'gemini-flash-latest'
]

@st.cache_resource
def get_model(api_key):
    genai.configure(api_key=api_key)
    for m_name in AVAILABLE_MODELS:
        try:
            model = genai.GenerativeModel(model_name=m_name)
            model.generate_content("ping")
            return model
        except Exception as e:
            continue
    return None

model = get_model(api_key)
if not model:
    st.error("Model bağlantısı başarısız.")
    st.stop()

# --- KNOWLEDGE BASE (SYSTEM PROMPT) ---
SYSTEM_INSTRUCTION = """
Sen uzman bir TOGAF 10 danışmanısın. 
Kurumsal mimarların TOGAF 10 sınavı ve profesyonel uygulamaları hakkındaki sorularını yanıtla.

KURALLAR:
1. TOGAF 10 dışında sorulara cevap verme.
2. Sadece resmi TOGAF 10 dökümanlarını baz al.
3. Profesyonel ve kısa yanıtlar ver.
4. Yanıtına ADM evresini (Phase A, B, C vb.) ekle.
"""

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    if current_usage >= MAX_DAILY_QUOTA_PER_IP:
        st.error(f"Günlük limit ({MAX_DAILY_QUOTA_PER_IP}) doldu.")
        st.stop()
    
    st.session_state.ip_usage[ip_hash] = current_usage + 1
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nKullanıcı: {prompt}")
            
            if response and response.text:
                full_response = response.text
                words = full_response.split()
                partial_text = ""
                for word in words:
                    partial_text += word + " "
                    message_placeholder.markdown(partial_text + "▌")
                    time.sleep(0.01)
                message_placeholder.markdown(full_response)
            else:
                st.error("Yanıt alınamadı.")
        except Exception as e:
            st.error(f"Hata: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.rerun()
