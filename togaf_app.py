import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURATION ---
ST_TITLE = "TOGAF 10 Kurumsal Asistan"
ST_ICON = "🏢"

# --- PAGE SETUP ---
st.set_page_config(page_title=ST_TITLE, page_icon=ST_ICON)
st.title(f"{ST_ICON} {ST_TITLE}")
st.markdown("""
TOGAF 10 Sertifikasyon sürecine hazırlanan çalışma arkadaşlarımız için özel olarak tasarlanmış yapay zeka asistanı.
Bu asistan sadece TOGAF 10 standartlarına ve ADM (Architecture Development Method) döngüsüne sadık kalarak yanıt verir.
""")

# --- SIDEBAR (Settings & Auth) ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    api_key = st.text_input("Gemini API Key", type="password")
    access_password = st.text_input("Uygulama Şifresi", type="password")
    
    st.divider()
    st.info("Kullanım Limiti: Kullanıcı başına günlük 20 sorgu tavsiye edilir.")

# --- AUTH CHECK ---
# Örnek şifre: 'ataraxia2026' (Sefa bunu değiştirebilir)
VALID_PASSWORD = "togaf" 

if not api_key:
    st.warning("Lütfen sidebar üzerinden Gemini API Key giriniz.")
    st.stop()

if access_password != VALID_PASSWORD:
    st.error("Lütfen geçerli bir Uygulama Şifresi giriniz.")
    st.stop()

# --- MODEL SETUP ---
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- KNOWLEDGE BASE (SYSTEM PROMPT) ---
# Sefa kaynakları yükledikçe bu kısım dinamik hale getirilebilir (RAG).
# Şimdilik TOGAF 10 odaklı güçlü bir System Prompt hazırlıyoruz.
SYSTEM_INSTRUCTION = """
Sen uzman bir TOGAF 10 (The Open Group Architecture Framework) danışmanısın. 
Görevin, kullanıcıların TOGAF 10 sınavı ve uygulaması hakkındaki sorularını yanıtlamaktır.

KURALLAR:
1. Sadece TOGAF 10 standartlarına, ADM döngüsüne (Preliminary, A-H Phase, Requirements Management) ve Series Guide'lara sadık kal.
2. Bilmediğin veya kaynaklarda olmayan bir şey sorulursa "Bu bilgi TOGAF 10 standart dökümanlarında yer almamaktadır" de.
3. Yanıtlarını kurumsal mimar terminolojisine uygun, net ve profesyonel bir dille ver.
4. Karmaşık kavramları açıklarken ADM döngüsü içindeki yerini belirt.
5. Kullanıcıya sınavda çıkabilecek ipuçlarını (Exam Tips) hatırlat.
"""

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("TOGAF hakkında ne sormak istersin?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Prepare prompt with system instruction
            # Not: Flash modeline her seferinde sistem talimatını ekliyoruz.
            chat = model.start_chat(history=[])
            response = chat.send_message(f"{SYSTEM_INSTRUCTION}\n\nKullanıcı Sorusu: {prompt}")
            
            # Simulate streaming
            for chunk in response.text.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"Bir hata oluştu: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": full_response})
