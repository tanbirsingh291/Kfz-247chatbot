import streamlit as st
import google.generativeai as genai
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. KONFIGURATION ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    # E-Mail Secrets
    email_sender = st.secrets["EMAIL_SENDER"]
    email_password = st.secrets["EMAIL_PASSWORD"]
    email_receiver = st.secrets["EMAIL_RECEIVER"]
    smtp_server = st.secrets["SMTP_SERVER"]
    smtp_port = st.secrets["SMTP_PORT"]
except:
    # Fallback für lokal
    api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ API Key fehlt! Bitte Secrets prüfen.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. E-MAIL FUNKTION ---
def send_email(chat_history):
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_receiver
    msg['Subject'] = "🚨 Neuer Unfall-Lead (via Lea Bot)"

    body = "Hallo Herr Rump,\n\nhier ist ein neuer Lead von Lea:\n\n"
    for message in chat_history:
        role = "KUNDE" if message["role"] == "user" else "LEA"
        clean_content = message['content'].replace("[MAIL_SENDEN]", "")
        body += f"{role}: {clean_content}\n\n"
    
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_sender, email_password)
        text = msg.as_string()
        server.sendmail(email_sender, email_receiver, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Fehler beim Mail-Versand: {e}")
        return False

# --- 3. SYSTEM PROMPT ---
system_instruction = """
Du bist 'Lea', die Assistentin des Kfz-Sachverständigenbüros Rump.
Deine Aufgabe: Daten aufnehmen (Name, Telefon, Auto, Schaden, Ort).
Sei kurz, empathisch und professionell.

WICHTIG: 
Sobald du Name und Telefonnummer des Kunden hast, füge am Ende deiner Antwort unauffällig diesen Code hinzu: [MAIL_SENDEN]
Diesen Code sieht der Kunde nicht, aber er löst den Versand an Herrn Rump aus.

Beispiel Ende: "Danke Herr Müller, ich habe alles notiert. Herr Rump ruft Sie morgen früh an. [MAIL_SENDEN]"
"""

# --- 4. MODELL STARTEN (Priorität: Gemini 2.5) ---
model = None
active_model_name = ""

# Liste der Modelle: Zuerst das gewünschte 2.5, dann Fallbacks
priority_list = [
    "gemini-2.5-flash",        # Wunsch-Modell
    "gemini-2.0-flash-exp",    # Alternative Bezeichnung
    "gemini-1.5-flash",        # Solider Fallback
    "gemini-pro"               # Letzte Rettung
]

for model_name in priority_list:
    try:
        # Versuch, das Modell zu laden
        test_model = genai.GenerativeModel(
            model_name=model_name, 
            system_instruction=system_instruction
        )
        # Wenn kein Fehler kommt, nehmen wir es!
        model = test_model
        active_model_name = model_name
        break
    except:
        continue

if model is None:
    st.error("Kritischer Fehler: Konnte kein KI-Modell verbinden.")
    st.stop()

# --- 5. UI & LOGIK ---
st.set_page_config(page_title="Rump Unfall-Hilfe", page_icon="🚗")
st.title("🚗 Unfall-Notdienst Rump")
st.caption(f"Ich bin Lea. (Powered by {active_model_name})")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Hallo! Hier ist der digitale Notdienst vom Büro Rump. Hatten Sie einen Unfall?"})
    st.session_state.chat_session = model.start_chat(history=[])
    st.session_state.mail_sent = False 

for msg in st.session_state.messages:
    content_display = msg["content"].replace("[MAIL_SENDEN]", "")
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.write(content_display)

if prompt := st.chat_input("Ihre Antwort..."):
    # User Nachricht anzeigen und speichern
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # KI Antwort generieren
    with st.chat_message("assistant"):
        try:
            response = st.session_state.chat_session.send_message(prompt)
            full_response = response.text
            
            # Prüfen ob Mail gesendet werden soll
            if "[MAIL_SENDEN]" in full_response and not st.session_state.mail_sent:
                with st.spinner("Sende Daten an Herrn Rump..."):
                    success = send_email(st.session_state.messages + [{"role": "assistant", "content": full_response}])
                    if success:
                        st.toast("✅ Lead gesichert! Mail ist raus.", icon="📧")
                        st.session_state.mail_sent = True
            
            # Text bereinigen und anzeigen
            display_text = full_response.replace("[MAIL_SENDEN]", "")
            st.write(display_text)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Ein Fehler ist aufgetreten: {e}")
