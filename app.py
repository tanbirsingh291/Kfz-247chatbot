import streamlit as st
import google.generativeai as genai
import os

# --- KONFIGURATION ---
# Versuche den Key aus den Streamlit Secrets zu laden
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # Fallback für lokale Tests (falls Umgebungsvariable gesetzt)
    api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ Kein API Key gefunden! Bitte in Streamlit Cloud unter 'Secrets' eintragen.")
    st.stop()

genai.configure(api_key=api_key)

# --- SYSTEM PROMPT ---
system_instruction = """
Du bist 'Lea', die virtuelle Assistentin des Kfz-Sachverständigenbüros Rump.
Deine Aufgabe: Unfallgeschädigte beruhigen und Daten aufnehmen.
Sei empathisch, kurz und professionell.

Führe den Nutzer Schritt für Schritt durch diese Punkte:
1. Name
2. Rückrufnummer
3. Fahrzeugmodell & Marke
4. Standort des Fahrzeugs
5. Art des Schadens (kurz)
6. Ist das Fahrzeug noch fahrbereit?

WICHTIG:
- Gib KEINE Rechtsberatung.
- Nenne KEINE Preise.
- Sobald du Name und Telefonnummer hast, gilt der Lead als gesichert.
- Am Ende: Bedanke dich und sage, dass Herr Rump sich ab 8:00 Uhr meldet.
"""

# --- MODELL STARTEN ---
# Wir nutzen Gemini 2.5 Flash wie gewünscht.
# Falls der Name in der API leicht anders ist, springt er auf 1.5 zurück, damit die App nicht abstürzt.
try:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=system_instruction
    )
except Exception as e:
    # Fallback, falls 2.5 noch Experimental-Status hat
    print(f"Switching to fallback model due to: {e}")
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )

# --- UI LAYOUT ---
st.set_page_config(page_title="Rump Unfall-Hilfe", page_icon="🚗")
st.title("🚗 Unfall-Notdienst Rump")
st.caption("Ich bin Lea. Wie kann ich Ihnen helfen?")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hallo! Hier ist der digitale Notdienst vom Büro Rump. Hatten Sie einen Unfall?"})
    st.session_state.chat_session = model.start_chat(history=[])

for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.write(msg["content"])

if prompt := st.chat_input("Ihre Antwort..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(prompt, stream=True)
            def stream_parser(stream):
                for chunk in stream:
                    yield chunk.text
            full_response = st.write_stream(stream_parser(response))
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Ein Fehler ist aufgetreten: {e}")
