import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta

# --- CONFIGURATION ---
ST_TITLE = "TOGAF 10 Kurumsal Mimari Asistanı"
ST_ICON = "🏢"
MAX_DAILY_QUOTA_PER_USER = 50  # Kişi başı günlük limit

# --- WHITELIST ---
# İzin verilen kullanıcılar (email veya tanımlayıcı)
ALLOWED_USERS = [
    "sefkaraoglu@gmail.com",
    "alfred.ataraxia@gmail.com",
]

# --- PAGE SETUP ---
st.set_page_config(page_title=ST_TITLE, page_icon=ST_ICON, layout="centered")

st.title(f"{ST_ICON} {ST_TITLE}")
st.caption("TOGAF 10 Standartları ve ADM Döngüsü Üzerine Uzmanlaşmış Kurumsal Destek Sistemi")

# --- AUTHENTICATION ---
# Basit whitelist kontrolü
if "user_identifier" not in st.session_state:
    st.session_state.user_identifier = None

if st.session_state.user_identifier is None:
    with st.form("auth_form"):
        st.markdown("### 🔐 Erişim için kimlik doğrulama")
        user_email = st.text_input("E-posta adresiniz:")
        submit = st.form_submit_button("Giriş")
        
        if submit and user_email:
            if user_email in ALLOWED_USERS:
                st.session_state.user_identifier = user_email
                st.rerun()
            else:
                st.error("Bu e-posta adresi yetkilendirilmemiş. Erişim reddedildi.")
                st.stop()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://www.opengroup.org/sites/default/files/togaf_logo.png", width=150)
    st.divider()
    st.markdown(f"**Kullanıcı:** {st.session_state.user_identifier}")
    st.markdown(f"**Günlük Limit:** {MAX_DAILY_QUOTA_PER_USER} Sorgu")
    
    # Kullanım istatistikleri
    if "usage_reset_date" not in st.session_state:
        st.session_state.usage_reset_date = datetime.now().date()
    
    # Günlük reset
    if st.session_state.usage_reset_date != datetime.now().date():
        st.session_state.daily_usage = 0
        st.session_state.usage_reset_date = datetime.now().date()
    
    if "daily_usage" not in st.session_state:
        st.session_state.daily_usage = 0
    
    remaining = MAX_DAILY_QUOTA_PER_USER - st.session_state.daily_usage
    st.progress(remaining / MAX_DAILY_QUOTA_PER_USER, text=f"Kalan: {remaining}/{MAX_DAILY_QUOTA_PER_USER}")
    
    if st.button("Çıkış"):
        st.session_state.user_identifier = None
        st.session_state.daily_usage = 0
        st.rerun()
    
    st.divider()
    st.info("Bu asistan resmi TOGAF 10 dökümantasyonu üzerine uzmanlaşmıştır.")

# --- API SETUP ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Sistem Yapılandırma Hatası: API anahtarı 'Secrets' içerisinde tanımlanmamış.")
    st.stop()

# --- MODEL SETUP ---
# Güncellenmiş model listesi
AVAILABLE_MODELS = [
    'gemini-2.0-flash-exp',
    'gemini-2.0-flash',
    'gemini-1.5-flash',
    'gemini-1.5-flash-8k',
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
        except Exception:
            continue
    return None

model = get_model(api_key)
if not model:
    st.error("Ücretsiz katman (Free Tier) kota limitlerine takıldınız veya uygun model bulunamadı.")
    st.stop()

# --- KNOWLEDGE BASE (SYSTEM PROMPT) ---
SYSTEM_INSTRUCTION = f"""
Sen uzman bir TOGAF 10 (The Open Group Architecture Framework) danışmanısın. 
Görevin, kurumsal mimarların TOGAF 10 sınavı ve profesyonel uygulamaları hakkındaki sorularını teknik bir dille yanıtlamaktır.

KRİTİK KISITLAMALAR VE KURALLAR:
1. ALAN DIŞI SORULAR: Eğer kullanıcı TOGAF 10, Kurumsal Mimari, ADM döngüsü veya ilgili standartlar dışında (yemek tarifi, hava durumu, genel sohbet, kodlama, siyaset vb.) herhangi bir şey sorarsa, ASLA cevap verme. Sadece şu cümleyi söyle: "Özür dilerim, ben sadece TOGAF 10 standartları ve Kurumsal Mimari konularında uzmanlaşmış bir asistanım. Lütfen bu alanlarla ilgili bir soru sorunuz."
2. KAYNAK: Sadece resmi TOGAF 10 dökümanlarını baz al.
3. ÜSLUP: Profesyonel, ciddi ve kurumsal bir dil kullan. Gereksiz hiçbir yorum yapma.
4. İPUCU: Yanıtlarının sonuna ilgili ADM evresini (Phase A, B, C vb.) veya döküman referansını ekle.
"""

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Sorunuzu buraya yazın..."):
    # Kişi başı limit kontrolü
    if st.session_state.daily_usage >= MAX_DAILY_QUOTA_PER_USER:
        st.error(f"Günlük {MAX_DAILY_QUOTA_PER_USER} sorgu limitine ulaştınız. Yarın tekrar deneyin.")
        st.stop()
    
    st.session_state.daily_usage += 1
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
                st.error("Model yanıt üretemedi.")
        except Exception as e:
            if "429" in str(e):
                st.error("Hız Sınırı (Rate Limit) Aşıldı. Lütfen 30 saniye bekleyip tekrar deneyin.")
            else:
                st.error(f"Sistem Hatası: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Sidebar'ı güncelle
    st.rerun()