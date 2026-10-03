import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Token de verificación (inventado por ti, debe coincidir con Meta)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ondera_secreto_123")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")

@app.route("/webhook", methods=['GET'])
def verify():
    """Meta verifica este endpoint para asegurarse de que eres tú"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFICADO")
        return challenge, 200
    else:
        return "Error de verificación", 403

@app.route("/webhook", methods=['POST'])
def webhook():
    """Recibe los mensajes de WhatsApp"""
    data = request.get_json()
    
    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if 'messages' in value:
            message = value['messages'][0]
            from_number = message['from']
            text = message['text']['body'].lower()
            
            print(f"Mensaje de {from_number}: {text}")
            
            # Respuesta de prueba (luego pondremos la IA)
            if 'hola' in text:
                respuesta = "¡Hola! Soy Onderi. ¿En qué puedo ayudarte?"
            else:
                respuesta = "Recibí tu mensaje. Pronto tendré mi cerebro de IA."
            
            # Enviar respuesta de vuelta por WhatsApp
            send_whatsapp_message(from_number, respuesta)
            
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

    return jsonify({"status": "ok"}), 200

def send_whatsapp_message(to, message):
    """Envía un mensaje de vuelta usando la API de WhatsApp"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"Respuesta de envío: {response.status_code}")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
