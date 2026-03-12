import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURATION ---
ST_TITLE = "TOGAF 10 Kurumsal Mimari Asistanı"
ST_ICON = "🏢"
MAX_DAILY_QUOTA = 60

# --- PAGE SETUP ---
st.set_page_config(page_title=ST_TITLE, page_icon=ST_ICON, layout="centered")

st.title(f"{ST_ICON} {ST_TITLE}")
st.caption("TOGAF 10 Standartları ve ADM Döngüsü Üzerine Uzmanlaşmış Kurumsal Destek Sistemi")

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://www.opengroup.org/sites/default/files/togaf_logo.png", width=150)
    st.divider()
    st.markdown(f"**Günlük Limit:** {MAX_DAILY_QUOTA} Sorgu")
    st.info("Bu asistan resmi TOGAF 10 dökümantasyonu üzerine uzmanlaşmıştır.")

# --- API SETUP ---
# API Key
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Sistem Yapılandırma Hatası: API anahtarı 'Secrets' içerisinde tanımlanmamış.")
    st.stop()

# --- MODEL SETUP ---
AVAILABLE_MODELS = ['gemini-1.5-flash', 'gemini-flash-latest', 'gemini-2.0-flash']

@st.cache_resource
def get_model(api_key):
    genai.configure(api_key=api_key)
    for m_name in AVAILABLE_MODELS:
        try:
            model = genai.GenerativeModel(model_name=m_name)
            # Modeli test et (boş bir prompt ile)
            model.generate_content("ping")
            return model
        except Exception:
            continue
    return None

model = get_model(api_key)

if not model:
    st.error("Ücretsiz katman (Free Tier) kota limitlerine takıldınız veya uygun model bulunamadı.")
    st.info("Lütfen birkaç dakika sonra tekrar deneyin veya farklı bir API anahtarı kullanın.")
    st.stop()

# --- KNOWLEDGE BASE (SYSTEM PROMPT) ---
SYSTEM_INSTRUCTION = f"""
Sen uzman bir TOGAF 10 (The Open Group Architecture Framework) danışmanısın. 
Görevin, kurumsal mimarların TOGAF 10 sınavı ve profesyonel uygulamaları hakkındaki sorularını teknik bir dille yanıtlamaktır.

TEMEL YÖNERGELER:
1. Kaynak: Sadece resmi TOGAF 10 standartlarını, ADM döngüsünü ve Open Group Series Guide'larını baz al.
2. Üslup: Profesyonel, kurumsal ve mimari odaklı bir dil kullan.
3. İpucu: Yanıtlarının sonuna ilgili ADM evresini (Phase A, B, C vb.) veya döküman referansını ekle.
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
            response = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nKullanıcı Sorusu: {prompt}")
            
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
                st.error("Model yanıt üretemedi. Kota aşılmış olabilir.")
        except Exception as e:
            if "429" in str(e):
                st.error("Hız Sınırı (Rate Limit) Aşıldı. Lütfen 30 saniye bekleyip tekrar deneyin.")
            else:
                st.error(f"Sistem Hatası: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
