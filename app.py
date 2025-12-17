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
# Zeigt klein an, welches Gehirn gerade läuft
st.caption(f"Ich bin Lea. (Powered by {active_model_name})")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role":
