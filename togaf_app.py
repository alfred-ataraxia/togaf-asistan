import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURATION ---
ST_TITLE = "TOGAF 10 Kurumsal Mimari Asistanı"
ST_ICON = "🏢"
MAX_DAILY_QUOTA = 60

# --- PAGE SETUP ---
st.set_page_config(page_title=ST_TITLE, page_icon=ST_ICON, layout="centered")

# Custom CSS for Corporate Look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stChatFloatingInputContainer {
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_stdio=True)

st.title(f"{ST_ICON} {ST_TITLE}")
st.caption("TOGAF 10 Standartları ve ADM Döngüsü Üzerine Uzmanlaşmış Kurumsal Destek Sistemi")

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://www.opengroup.org/sites/default/files/togaf_logo.png", width=150)
    st.header("🔒 Erişim Kontrolü")
    access_password = st.text_input("Giriş Şifresi", type="password")
    
    st.divider()
    st.markdown(f"**Günlük Limit:** {MAX_DAILY_QUOTA} Sorgu")
    st.info("Bu asistan resmi TOGAF 10 dökümantasyonu üzerine uzmanlaşmıştır.")

# --- AUTH & API SETUP ---
VALID_PASSWORD = "togaf"

if access_password != VALID_PASSWORD:
    st.warning("Lütfen yetkili giriş şifresini giriniz.")
    st.stop()

# API Key - SECURE RETRIEVAL FROM STREAMLIT SECRETS
# Kullanıcı bu anahtarı Streamlit Cloud panelinde "Secrets" kısmına eklemelidir.
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Sistem Yapılandırma Hatası: API anahtarı 'Secrets' içerisinde tanımlanmamış.")
    st.info("Yönetici Notu: Lütfen Streamlit Cloud ayarlarından GEMINI_API_KEY değişkenini tanımlayın.")
    st.stop()

# --- MODEL SETUP ---
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- KNOWLEDGE BASE (SYSTEM PROMPT) ---
SYSTEM_INSTRUCTION = f"""
Sen uzman bir TOGAF 10 (The Open Group Architecture Framework) danışmanısın. 
Görevin, kurumsal mimarların TOGAF 10 sınavı ve profesyonel uygulamaları hakkındaki sorularını teknik bir dille yanıtlamaktır.

TEMEL YÖNERGELER:
1. Kaynak: Sadece resmi TOGAF 10 standartlarını, ADM döngüsünü ve Open Group Series Guide'larını baz al.
2. Üslup: Profesyonel, kurumsal ve mimari odaklı bir dil kullan.
3. Kısıtlama: TOGAF dışı genel soruları reddet.
4. İpucu: Yanıtlarının sonuna ilgili ADM evresini (Phase A, B, C vb.) veya döküman referansını ekle.
"""

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    if len(st.session_state.messages) / 2 >= MAX_DAILY_QUOTA:
        st.error(f"Günlük {MAX_DAILY_QUOTA} sorgu limitine ulaştınız.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            chat = model.start_chat(history=[])
            response = chat.send_message(f"{SYSTEM_INSTRUCTION}\n\nKullanıcı Sorusu: {prompt}")
            
            for chunk in response.text.split():
                full_response += chunk + " "
                time.sleep(0.02)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"Sistem Hatası: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
